import re


class MessageClassifier:
    """
    Класс MessageClassifier предназначен для классификации сообщений от пользователя
    с использованием лемматизации pymorphy2 и обширного набора классов на основе SCs-файлов.

    Основная задача — определить класс сообщения, извлечь при необходимости сущности и их классы,
    и вернуть результат в стандартизированной структуре.
    """

    def __init__(self):
        self._morph = None
        self._keyword_sets = {}

    def _get_morph(self):
        """Ленивая инициализация pymorphy2"""
        if self._morph is None:
            import pymorphy2
            self._morph = pymorphy2.MorphAnalyzer()
        return self._morph

    def _lemmatize(self, text: str) -> str:
        """
        Лемматизирует русскоязычный текст с помощью pymorphy2.
        Возвращает строку с леммами слов, разделённых пробелами.
        Не-RU слова оставляет как есть в нижнем регистре.
        """
        morph = self._get_morph()
        words = re.findall(r'[а-яА-ЯёЁa-zA-Z]+', text)
        lemmas = []
        for word in words:
            # Если слово содержит кириллицу — лемматизируем
            if re.search(r'[а-яА-ЯёЁ]', word):
                parsed = morph.parse(word)[0]
                lemmas.append(parsed.normal_form)
            else:
                lemmas.append(word.lower())
        return ' '.join(lemmas)

    def _pre_compute_keywords(self, keywords: list[str]) -> set:
        """
        Предварительно лемматизирует список ключевых слов и возвращает set для быстрого поиска.
        Кэширует результат.
        """
        key = tuple(keywords)
        if key not in self._keyword_sets:
            lemmatized = set()
            for kw in keywords:
                kw_lemma = self._lemmatize(kw).strip().lower()
                if kw_lemma and ' ' not in kw_lemma:
                    lemmatized.add(kw_lemma)
                elif kw_lemma:
                    # Multi-word keyword: store as a tuple for phrase matching
                    lemmatized.add(kw_lemma)
            self._keyword_sets[key] = lemmatized
        return self._keyword_sets[key]

    def _match_any_keyword(self, lemmatized_text: str, keywords: list[str]) -> bool:
        """
        Проверяет, содержит ли лемматизированный текст хотя бы одно из ключевых слов.
        Использует точное совпадение по словам (не подстроки), чтобы избежать
        ложных срабатываний (например, 'без' внутри 'безопасность').
        """
        token_set = set(lemmatized_text.lower().split())
        text_lower = lemmatized_text.lower()
        lemma_set = self._pre_compute_keywords(keywords)
        for kw_lemma in lemma_set:
            if ' ' in kw_lemma:
                # Multi-word: use substring matching on the full lemmatized text
                if kw_lemma in text_lower:
                    return True
            else:
                # Single word: use exact token matching
                if kw_lemma in token_set:
                    return True
        return False

    def _match_any_pattern(self, message: str, patterns: list[str]) -> bool:
        """
        Проверяет, соответствует ли сообщение хотя бы одному regex-шаблону (без учёта регистра).
        """
        for pattern in patterns:
            if re.search(pattern, message, re.IGNORECASE | re.DOTALL):
                return True
        return False

    def classify(self, message: str, message_author_class: str, message_history: list[str]) -> tuple[str, dict, set]:
        """
        Классифицирует текстовое сообщение, исходя из его содержания и класса отправителя.

        Параметры
        ----------
        message : str
            Текст сообщения.
        message_author_class : str
            Класс автора (например: "concept_user").
        message_history : list[str]
            История предыдущих сообщений пользователя для контекстного анализа.

        Возвращает
        ----------
        tuple[str, dict, set]
            (идентификатор класса сообщения, словарь сущностей, множество классов контекстных сущностей)
        """
        if message_author_class != "concept_user":
            return ("concept_unknown_message", {}, set())

        # Лемматизируем исходное сообщение для дальнейшего анализа
        lemmatized = self._lemmatize(message)

        # --- 1. Прощание (farewell) ---
        if self._match_any_pattern(message, [
            r'^пока.*$',
            r'^до свидания.*$',
        ]) or self._match_any_keyword(lemmatized, [
            'пока', 'до свидания', 'прощай', 'увидимся',
            'всего доброго', 'удачи', 'бай',
        ]):
            return ("concept_user_message_about_farewell", {}, set())

        # --- 2. Отмена (cancel) ---
        if self._match_any_pattern(message, [
            r'^отмена.*$',
            r'^не надо.*$',
            r'^передумал.*$',
        ]) or self._match_any_keyword(lemmatized, [
            'отмена', 'отменить', 'не надо', 'передумать',
        ]):
            return ("concept_user_message_about_cancel", {}, set())

        # --- 3. Перезапуск (restart) ---
        if self._match_any_pattern(message, [
            r'^нач(ни|нём)\s+(сначала|заново).*$',
            r'^(перезапусти|рестарт).*$',
        ]) or self._match_any_keyword(lemmatized, [
            'сначала', 'заново', 'перезапуск', 'рестарт',
            'начать сначала', 'начать заново',
        ]):
            return ("concept_user_message_about_restart", {}, set())

        # --- 4. Приветствие (greeting) ---
        if self._match_any_pattern(message, [
            r'^привет.*$',
            r'^здравствуй.*$',
            r'^добр(ое|ый|ая).*$',
        ]) or self._match_any_keyword(lemmatized, [
            'привет', 'здравствуйте', 'салют', 'здорово',
            'добрый', 'доброе', 'приветствовать',
        ]):
            return ("concept_user_message_about_greeting", {}, set())

        # --- 5. Неформальное приветствие / как дела ---
        if self._match_any_keyword(lemmatized, [
            'как дела', 'как ты', 'как жизнь', 'чё как',
        ]):
            return ("concept_user_message_about_casual_greeting", {}, set())

        # --- 6. Запрос навыков (skills) ---
        if self._match_any_pattern(message, [
            r'^что ты умеешь.*$',
            r'^что ты можешь.*$',
            r'^какие (у тебя )?(функции|навыки|возможности).*$',
        ]) or self._match_any_keyword(lemmatized, [
            'уметь', 'мочь', 'навык', 'возможность',
            'функция', 'что ты',
        ]):
            return ("concept_user_message_about_skills", {}, set())

        # --- 7. Помощь (help) ---
        if self._match_any_pattern(message, [
            r'^помоги.*$',
            r'^нужна помощь.*$',
            r'^мне нужна помощь.*$',
            r'^я не понимаю.*$',
            r'^подскажи.*$',
        ]) or self._match_any_keyword(lemmatized, [
            'помощь', 'помочь', 'подсказать',
            'не понимать', 'сложно', 'трудно', 'что делать',
        ]):
            return ("concept_user_message_about_help", {}, set())

        # --- 8. Шаги рецепта (recipe_step) ---
        if self._match_any_pattern(message, [
            r'^дальше.*$',
            r'^следующий.*$',
            r'^назад.*$',
            r'^предыдущий.*$',
        ]) or self._match_any_keyword(lemmatized, [
            'дальше', 'далее', 'следующий', 'шаг',
            'назад', 'предыдущий', 'вернуться', 'продолжить',
            'следующий шаг',
        ]):
            return ("concept_user_message_about_recipe_step", {}, set())

        # --- 9. Поиск рецепта (recipe_search) ---
        if self._match_any_pattern(message, [
            r'^что (можно |бы )(приготовить|сделать|поесть).*$',
            r'^найди рецепт.*$',
            r'^(как |)(приготовить|сварить|пожарить|испечь).*$',
        ]) or self._match_any_keyword(lemmatized, [
            'рецепт', 'приготовить', 'сделать', 'блюдо',
            'сварить', 'пожарить', 'испечь',
            'что можно', 'найти', 'подобрать', 'предложить',
        ]):
            return ("concept_user_message_about_recipe_search", {}, set())

        # --- 10. Информация о блюде (cooking_info) ---
        if self._match_any_pattern(message, [
            r'^сколько (калорий|времени).*$',
            r'^(какая|какое) (сложность|время).*$',
        ]) or self._match_any_keyword(lemmatized, [
            'калория', 'калорийность', 'время', 'минута',
            'сложность', 'порция', 'ингредиент', 'состав',
            'описание', 'сколько',
        ]):
            return ("concept_user_message_about_cooking_info", {}, set())

        # --- 11. Ингредиенты (ingredients) ---
        if self._match_any_keyword(lemmatized, [
            'есть', 'иметься', 'добавить', 'положить',
            'купить', 'найти', 'убрать', 'удалить',
            'выбросить', 'нет', 'показать', 'список',
            'какой', 'очистить',
        ]):
            return ("concept_user_message_about_ingredients", {}, set())

        # --- 12. Предпочтения (preferences) ---
        if self._match_any_pattern(message, [
            r'^у меня аллергия.*$',
            r'^я не (ем|люблю).*$',
            r'^(мои |)(предпочтения|диета).*$',
            r'^без .*$',
        ]) or self._match_any_keyword(lemmatized, [
            'аллергия', 'не есть', 'не любить', 'предпочитать',
            'исключить', 'диета', 'веган', 'вегетарианец',
            'без', 'нельзя',
        ]):
            return ("concept_user_message_about_preferences", {}, set())

        # --- 13. Фото (photo) ---
        if self._match_any_keyword(lemmatized, [
            'фото', 'фотография', 'снимок', 'изображение',
            'картинка', 'посмотри', 'распознать',
        ]):
            return ("concept_user_message_about_photo", {}, set())

        # --- 14. Еда общее (food) ---
        if self._match_any_pattern(message, [
            r'^(чего|что).*(еда|поесть).*$',
            r'^еда.*$',
            r'^(поесть|покушать|кушать).*$',
        ]) or self._match_any_keyword(lemmatized, [
            'еда', 'есть', 'кушать', 'хавка',
        ]):
            return ("concept_user_message_about_food", {}, set())

        # --- 15. Запрос определения понятия (concept_information) ---
        concept_info_match = re.search(r'что такое\s+(.+)', message, re.IGNORECASE)
        if concept_info_match:
            entity = concept_info_match.group(1).strip()
            return ("concept_user_message_about_searching_concept_information", {"concept": entity}, set())

        # --- 16. Неизвестное сообщение ---
        return ("concept_unknown_message", {}, set())
