import re
import pymorphy3


# ---------------------------------------------------------------------------
# Категории (числовые классы):
# 0 - unknown
# 1 - greeting
# 2 - skills
# 3 - add ingredient
# 4 - del ingredient
# 5 - view ingredients
# 6 - preference
# 7 - allergy
# 8 - search by ingredients (рецепты)
# 9 - select ingredient (выбор из предложенных)
# 10 - recipe step (пошаговый рецепт)
# ---------------------------------------------------------------------------

CATEGORY_UNKNOWN = 0
CATEGORY_GREETING = 1
CATEGORY_SKILLS = 2
CATEGORY_ADD_INGREDIENT = 3
CATEGORY_DEL_INGREDIENT = 4
CATEGORY_VIEW_INGREDIENTS = 5
CATEGORY_PREFERENCE = 6
CATEGORY_ALLERGY = 7
CATEGORY_SEARCH_RECIPE = 8
CATEGORY_SELECT_INGREDIENT = 9

STOP_WORDS = {
    "и", "в", "во", "не", "что", "он", "на", "я", "с", "со",
    "как", "а", "то", "все", "она", "так", "его", "но", "да",
    "ты", "к", "у", "же", "вы", "за", "бы", "по", "только",
    "ее", "мне", "было", "вот", "от", "меня", "еще", "нет",
    "о", "из", "ему", "теперь", "когда", "даже", "ну", "ли",
    "если", "уже", "или", "ни", "быть", "был", "него", "вас",
    "нибудь", "опять", "уж", "вам", "ведь", "там", "потом",
    "себя", "ничего", "ей", "может", "они", "тут", "где",
    "есть", "надо", "ней", "для", "мы", "тебя", "их", "чем",
    "была", "сам", "чтоб", "без", "будто", "чего", "раз",
    "тоже", "себе", "под", "будет", "ж", "тогда", "кто", "этот",
    "того", "потому", "этого", "какой", "совсем", "ним", "здесь",
    "этом", "один", "почти", "мой", "тем", "чтобы", "нее",
    "сейчас", "были", "куда", "зачем", "всех", "никогда",
    "можно", "при", "наконец", "два", "об", "другой", "хоть",
    "после", "над", "больше", "тот", "через", "эти", "нас",
    "про", "всего", "них", "какая", "много", "разве", "три",
    "эту", "моя", "впрочем", "хорошо", "свою", "этой", "перед",
    "иногда", "лучше", "чуть", "том", "такой", "им",
    "более", "всегда", "конечно", "всю", "между",
    "это", "твой", "наш", "ваш", "свой",
}

RULES = [
    {
        "category": CATEGORY_GREETING,
        "keywords": [
            "привет", "здравствуй", "здравствовать", "добрый",
            "хай", "хелло", "йоу", "салют",
            "доброе утро", "добрый день", "добрый вечер", "добрый ночь",
        ],
        "patterns": [
            r"^привет",
            r"^добр(ый|ая|ое|ой|ого|ому|ым|ом)",
            r"^здравствуй",
        ],
        "weight": 2.0,
    },
    {
        "category": CATEGORY_SKILLS,
        "keywords": [
            "уметь", "умеешь", "умение", "мочь", "можешь",
            "научить", "помощь", "помочь", "что делать",
            "что можешь", "что умеешь", "функция",
            "возможность", "команда",
        ],
        "patterns": [
            r"что (ты )?(умеешь|можешь|уметь|мочь)",
            r"чем (можешь|умеешь) (помочь|помощь)",
            r"(помощь|помочь|помощи)",
            r"(функция|команда|возможность)",
        ],
        "weight": 1.8,
    },
    {
        "category": CATEGORY_ADD_INGREDIENT,
        "keywords": [
            "добавить", "добавляю", "довать", "взять",
            "включить", "положить", "поставить",
            "купить", "иметь", "есть",
        ],
        "patterns": [
            r"(добавь|добавить|добавлять|довать)",
            r"(включи|включить|включать)",
            r"у меня есть",
            r"я (взял|взяла|купил|купила|имею)",
            r"(положи|положить|поставь|поставить)",
        ],
        "weight": 1.5,
        "negative_keywords": ["удалить", "убрать", "убирать", "нет"],
    },
    {
        "category": CATEGORY_DEL_INGREDIENT,
        "keywords": [
            "удалить", "убрать", "убирать", "снять",
            "исключить", "выбросить",
        ],
        "patterns": [
            r"(удали|удалить|удалять)",
            r"(убери|убрать|убирать)",
            r"(сними|снять|снимать)",
            r"(исключи|исключить|исключать)",
            r"без \w+",
            r"нет .*(ингредиент|продукт)",
        ],
        "weight": 1.5,
    },
    {
        "category": CATEGORY_VIEW_INGREDIENTS,
        "keywords": [
            "показать", "показывать", "посмотреть",
            "просмотр", "список", "что есть",
            "какие ингредиенты", "мои ингредиенты",
        ],
        "patterns": [
            r"(покажи|показать|показывать) .*(ингредиент|продукт|список)",
            r"(посмотри|посмотреть|просмотреть) .*(ингредиент|продукт)",
            r"(мои|текущие|список) (ингредиент|продукт)",
            r"что (у меня )?есть",
            r"какие (ингредиент|продукт)",
        ],
        "weight": 1.5,
        "negative_keywords": ["рецепт", "приготовить"],
    },
    {
        "category": CATEGORY_PREFERENCE,
        "keywords": [
            "люблю", "нравиться", "предпочитать", "вкусный",
            "вкус", "сладкий", "солёный", "острый", "кислый",
            "вегетарианский", "веганский", "диета", "полезный",
            "низкокалорийный", "постный", "глютен",
            "без сахара", "без соли",
        ],
        "patterns": [
            r"(люблю|нравиться|предпочитать)",
            r"(сладк|солён|остр|кисл|горьк)",
            r"(вегетариан|веган|постн|диет)",
            r"(полезн|низкокалорийн|без сахара|без соли)",
            r"я (люблю|предпочитаю|не ем|не едим)",
        ],
        "weight": 1.4,
    },
    {
        "category": CATEGORY_ALLERGY,
        "keywords": [
            "аллергия", "аллергик", "аллерген", "непереносимость",
            "нельзя", "запрещено", "нельзя есть",
            "реакция", "сыпь", "отёк",
        ],
        "patterns": [
            r"(аллерги|аллерген|аллергик)",
            r"(непереносимость|непереносимый)",
            r"у меня аллерги",
            r"(нельзя|запрещено|противопоказан)",
            r"я не (могу|еду|ем|беру) .*(из-за|аллерг)",
        ],
        "weight": 2.0,
    },
    {
        "category": CATEGORY_SEARCH_RECIPE,
        "keywords": [
            "приготовить", "рецепт", "сварить", "пожарить",
            "сделать блюдо", "что приготовить",
            "что сварить", "что пожарить",
        ],
        "patterns": [
            r"(что|чем) (приготовить|сварить|пожарить|сделать)",
            r"(приготовь|свари|пожари|сделай)",
            r"(рецепт|блюдо) .*(из|с|на основе)",
            r"(найди|найти|покажи) .*(рецепт|блюдо)",
            r"(что можно) (приготовить|сделать|сварить)",
            r"(есть (рецепт|блюдо))",
        ],
        "weight": 1.7,
    },
    {
        "category": CATEGORY_SELECT_INGREDIENT,
        "keywords": ["выбрать", "выбор", "беру", "подходит", "возьму"],
        "patterns": [
            r"^(да|нет|ок|ага|угу|давай)$",
            r"^(выбрать?|беру|возьму|подходит|подойдёт)$",
            r"^(один|два|три|четыре|пять)$",
            r"^\d+$",
        ],
        "weight": 1.3,
    },
]


class MessageClassifier:
    def __init__(self):
        self.morph = pymorphy3.MorphAnalyzer()
        self.rules = RULES

    def classify(self, text, user_ingredients=None, offered_ingredients=None, current_recipe_step=None):
        normalized = self.normalize(text)
        lemmas = self.tokenize(text)
        lemma_set = set(lemmas)

        best_category = CATEGORY_UNKNOWN
        best_score = 0.0

        for rule in self.rules:
            if self.rule_matches(rule, lemma_set, normalized):
                if rule["weight"] > best_score:
                    best_score = rule["weight"]
                    best_category = rule["category"]

        if best_category == CATEGORY_UNKNOWN:
            best_category, best_score = self.contextual_rules(
                lemma_set, normalized, offered_ingredients, current_recipe_step)

        return best_category, self.extract_entities(text, best_category)
    
    def normalize(self, text):
        words = re.findall(r"[а-яёА-ЯЁ]+", text.lower())
        return " ".join(self.morph.parse(w)[0].normal_form for w in words)

    def tokenize(self, text):
        words = re.findall(r"[а-яёА-ЯЁ]+", text.lower())
        lemmas = []
        for w in words:
            lemma = self.morph.parse(w)[0].normal_form
            if lemma not in STOP_WORDS:
                lemmas.append(lemma)
        return lemmas

    def rule_matches(self, rule, lemma_set, normalized_text):
        negative = rule.get("negative_keywords", [])
        if negative and lemma_set & set(negative):
            return False

        keyword_hit = False
        for kw in rule["keywords"]:
            if " " in kw:
                if kw in normalized_text:
                    keyword_hit = True
                    break
            elif kw in lemma_set:
                keyword_hit = True
                break

        pattern_hit = False
        for pat in rule["patterns"]:
            if re.search(pat, normalized_text):
                pattern_hit = True
                break

        return keyword_hit or pattern_hit

    def contextual_rules(self, lemma_set, normalized_text, offered_ingredients, current_recipe_step):
        if offered_ingredients:
            stripped = normalized_text.strip()
            if (
                stripped in {"да", "нет", "ок", "ага", "угу", "давай", "беру", "возьму"}
                or re.match(r"^\d+$", stripped)
            ):
                return CATEGORY_SELECT_INGREDIENT, 1.5

            if lemma_set & set(offered_ingredients):
                return CATEGORY_SELECT_INGREDIENT, 1.2

        return CATEGORY_UNKNOWN, 0.0

    def extract_entities(self, text, category):
        entities = {}

        if category in (
            CATEGORY_ADD_INGREDIENT,
            CATEGORY_DEL_INGREDIENT,
            CATEGORY_SEARCH_RECIPE,
            CATEGORY_SELECT_INGREDIENT,
        ):
            nouns = self.extract_nouns(text, {"accs", "gent", "datv", "ablt", "loct"})
            if nouns:
                entities["ingredient"] = nouns

        if category == CATEGORY_ALLERGY:
            entities["allergen"] = self.extract_nouns(text, {"gent", "datv", "accs", "loct", "ablt"})

        if category == CATEGORY_PREFERENCE:
            entities["preference"] = self.extract_nouns(text, {"accs", "gent", "datv", "loct"})

        return entities

    def extract_nouns(self, text, cases=None):
        tokens = re.findall(r"[а-яёА-ЯЁ]+", text.lower())
        result = []

        for token in tokens:
            parsed = self.morph.parse(token)[0]
            if cases and parsed.tag.POS != "NOUN":
                continue
            if cases and parsed.tag.case not in cases:
                continue
            if parsed.normal_form in STOP_WORDS:
                continue
            result.append(parsed.normal_form)
        
        seen = set()
        unique = []
        for lemma in result:
            if lemma not in seen:
                seen.add(lemma)
                unique.append(lemma)

        return unique
