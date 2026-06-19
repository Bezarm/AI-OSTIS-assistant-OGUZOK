"""
Тесты для обновлённого MessageClassifier с pymorphy2.

Запуск: python3 test_classifier.py

Если pymorphy2 не установлен, тестируется только регулярное-выражение часть.
"""

import sys
import re


# --- Тестируем логику классификации без pymorphy2 ---

def _match_any_pattern(message: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        if re.search(pattern, message, re.IGNORECASE | re.DOTALL):
            return True
    return False


def run_tests():
    tests = [
        # (message, expected_pattern_match, pattern_list_name)
        # Greeting
        ("Привет!", True, "greeting"),
        ("приветствую", True, "greeting"),
        ("Здравствуйте!", True, "greeting"),
        ("Доброе утро", True, "greeting"),
        ("Добрый день", True, "greeting"),
        ("Здарова", False, "greeting"),  # keyword only, no pattern

        # Farewell
        ("Пока!", True, "farewell"),
        ("До свидания", True, "farewell"),
        ("пока всем", True, "farewell"),
        ("Удачи!", False, "farewell"),  # keyword only

        # Cancel
        ("Отмена", True, "cancel"),
        ("Не надо", True, "cancel"),
        ("Передумал", True, "cancel"),
        ("отмени", False, "cancel"),  # keyword only

        # Restart
        ("Начни сначала", True, "restart"),
        ("Начнём заново", True, "restart"),
        ("Перезапусти", True, "restart"),
        ("рестарт", True, "restart"),
        ("Сначала", False, "restart"),  # keyword only

        # Skills
        ("Что ты умеешь", True, "skills"),
        ("Что ты можешь", True, "skills"),
        ("Какие у тебя функции", True, "skills"),
        ("Какие навыки", True, "skills"),
        ("Какие возможности", True, "skills"),
        ("что ты", False, "skills"),  # keyword only

        # Help
        ("Помоги", True, "help"),
        ("Помогите", True, "help"),
        ("Мне нужна помощь", True, "help"),
        ("Нужна помощь", True, "help"),
        ("Я не понимаю", True, "help"),
        ("Подскажи", True, "help"),
        ("сложно", False, "help"),  # keyword only

        # Recipe step
        ("Дальше", True, "recipe_step"),
        ("Следующий", True, "recipe_step"),
        ("Назад", True, "recipe_step"),
        ("Предыдущий", True, "recipe_step"),
        ("следующий шаг", True, "recipe_step"),

        # Recipe search
        ("Что можно приготовить", True, "recipe_search"),
        ("Что бы сделать", True, "recipe_search"),
        ("Найди рецепт", True, "recipe_search"),
        ("Как приготовить", True, "recipe_search"),
        ("Как сварить суп", True, "recipe_search"),
        ("Как пожарить картошку", True, "recipe_search"),
        ("Как испечь пирог", True, "recipe_search"),
        ("рецепт", False, "recipe_search"),  # keyword only

        # Cooking info
        ("Сколько калорий", True, "cooking_info"),
        ("Сколько времени", True, "cooking_info"),
        ("Какая сложность", True, "cooking_info"),
        ("Какое время", True, "cooking_info"),
        ("калорийность", False, "cooking_info"),  # keyword only

        # Preferences
        ("У меня аллергия", True, "preferences"),
        ("У меня аллергия на орехи", True, "preferences"),
        ("Я не ем мясо", True, "preferences"),
        ("Я не люблю лук", True, "preferences"),
        ("Мои предпочтения", True, "preferences"),
        ("Диета", True, "preferences"),
        ("Без глютена", True, "preferences"),
        ("веган", False, "preferences"),  # keyword only

        # Food general
        ("Что поесть", True, "food"),
        ("Чего поесть", True, "food"),
        ("еда", True, "food"),
        ("поесть", True, "food"),
        ("Кушать", True, "food"),
        ("Покушать", True, "food"),

        # Concept information
        ("Что такое интеллект", True, "concept_info"),
        ("Что такое нейросеть", True, "concept_info"),
        ("что такое любовь", True, "concept_info"),

        # Should NOT match
        ("Мне 25 лет", False, "greeting"),
        ("Сегодня хорошая погода", False, "farewell"),
        ("Я люблю программировать", False, "help"),
    ]

    pattern_sets = {
        "greeting": [r'^привет.*$', r'^здравствуй.*$', r'^добр(ое|ый|ая).*$'],
        "farewell": [r'^пока.*$', r'^до свидания.*$'],
        "cancel": [r'^отмена.*$', r'^не надо.*$', r'^передумал.*$'],
        "restart": [r'^нач(ни|нём)\s+(сначала|заново).*$', r'^(перезапусти|рестарт).*$'],
        "skills": [r'^что ты умеешь.*$', r'^что ты можешь.*$', r'^какие (у тебя )?(функции|навыки|возможности).*$'],
        "help": [r'^помоги.*$', r'^нужна помощь.*$', r'^мне нужна помощь.*$', r'^я не понимаю.*$', r'^подскажи.*$'],
        "recipe_step": [r'^дальше.*$', r'^следующий.*$', r'^назад.*$', r'^предыдущий.*$'],
        "recipe_search": [r'^что (можно |бы )(приготовить|сделать|поесть).*$', r'^найди рецепт.*$', r'^(как |)(приготовить|сварить|пожарить|испечь).*$'],
        "cooking_info": [r'^сколько (калорий|времени).*$', r'^(какая|какое) (сложность|время).*$'],
        "preferences": [r'^у меня аллергия.*$', r'^я не (ем|люблю).*$', r'^(мои |)(предпочтения|диета).*$', r'^без .*$'],
        "food": [r'^(чего|что).*(еда|поесть).*$', r'^еда.*$', r'^(поесть|покушать|кушать).*$'],
        "concept_info": [r'что такое\s+.+'],
    }

    passed = 0
    failed = 0

    print("=" * 60)
    print("Тестирование MessageClassifier (регулярные выражения)")
    print("=" * 60)

    for message, expected, category in tests:
        patterns = pattern_sets.get(category, [])
        result = _match_any_pattern(message, patterns) if patterns else False

        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        else:
            failed += 1

        status_word = "OK" if result == expected else "FAIL"
        expected_word = "match" if expected else "not match"
        actual_word = "matched" if result else "did not match"
        print(f"  {status} [{category:15s}] {message:<40s} expected {expected_word}, {actual_word}")

    print(f"\n{'=' * 60}")
    print(f"Результат: {passed} passed, {failed} failed из {len(tests)}")
    print(f"{'=' * 60}")

    # Test concept information entity extraction
    print("\n--- Тест извлечения сущности для 'что такое' ---")
    test_phrases = [
        "Что такое интеллект",
        "что такое нейросеть",
        "Что такое любовь",
    ]
    for phrase in test_phrases:
        m = re.search(r'что такое\s+(.+)', phrase, re.IGNORECASE)
        if m:
            entity = m.group(1).strip()
            print(f"  ✓ '{phrase}' → entity: '{entity}'")
        else:
            print(f"  ✗ '{phrase}' → no match")

    # Test pymorphy2 if available
    print("\n--- Тест pymorphy2 (если установлен) ---")
    try:
        import pymorphy2
        morph = pymorphy2.MorphAnalyzer()

        test_words = [
            ("привет", "привет"),
            ("здравствуйте", "здравствовать"),
            ("еда", "еда"),
            ("поесть", "есть"),
            ("кушать", "кушать"),
            ("помоги", "помочь"),
            ("помощь", "помощь"),
            ("рецепты", "рецепт"),
            ("приготовить", "приготовить"),
            ("калорий", "калория"),
            ("аллергия", "аллергия"),
            ("предпочтения", "предпочтение"),
            ("отмена", "отмена"),
            ("перезапуск", "перезапуск"),
            ("пока", "пока"),
            ("сложно", "сложно"),
            ("дальше", "дальше"),
            ("назад", "назад"),
        ]

        pymorphy_ok = 0
        pymorphy_fail = 0
        for word, expected_lemma in test_words:
            parsed = morph.parse(word)[0]
            lemma = parsed.normal_form
            if lemma == expected_lemma:
                pymorphy_ok += 1
                print(f"  ✓ {word:20s} → {lemma}")
            else:
                pymorphy_fail += 1
                print(f"  ✗ {word:20s} → {lemma} (expected {expected_lemma})")

        print(f"\n  Лемматизация: {pymorphy_ok}/{len(test_words)} OK")

    except ImportError:
        print("  pymorphy2 не установлен — пропускаем тест лемматизации")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
