import re
import pymorphy3

from sc_kpm import ScKeynodes
from sc_kpm.utils import get_element_system_identifier
from sc_client import client as c
from sc_client.models import ScTemplate
from sc_client.constants import sc_type 

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
# 8 - search by ingredients
# 9 - select recipe
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
CATEGORY_SELECT_RECIPE = 9

STOP_WORDS = {
    "и", "в", "во", "не", "он", "на", "я", "с", "со",
    "а", "то", "все", "она", "так", "его", "но", "да",
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
        "weight": 1.3,
    },
    {
        "category": CATEGORY_SKILLS,
        "keywords": [
            "уметь", "умение", "мочь",
            "научить", "помощь", "помочь",
            "что делать", "что можешь", "что умеешь",
            "функция", "возможность", "команда",
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
            "добавить", "добавлять", "довать", "взять",
            "включить", "положить", "поставить",
            "купить", "иметь",
        ],
        "patterns": [
            r"(добавь|добавить|добавлять|довать)",
            r"(включи|включить|включать)",
            r"у меня есть",
            r"я (взял|взяла|купил|купила|имею)",
            r"(положи|положить|поставь|поставить)",
        ],
        "weight": 1.4,
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
        "weight": 1.4,
    },
    {
        "category": CATEGORY_VIEW_INGREDIENTS,
        "keywords": [
            "показать", "показывать", "посмотреть",
            "просмотр", "список",
            "что есть", "какие ингредиенты", "мои ингредиенты",
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
            "любить", "нравиться", "предпочитать", "вкусный",
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
            r"(найди|найти|покажи|предложи) .*(рецепт|блюдо)",
            r"(что можно) (приготовить|сделать|сварить)",
            r"(есть (рецепт|блюдо))",
        ],
        "weight": 1.7,
    },
    {
        "category": CATEGORY_SELECT_RECIPE,
        "keywords": ["рецепт", "блюдо", "как приготовить", "выбрать", "выбор"],
        "patterns": [
            r"рецепт .*(картошк|пельмен|сырник|омлет|гречк|макарон)",
            r"(приготовь|сделай|свари|пожари) .*(картошк|пельмен|сырник|омлет|гречк|макарон)",
            r"(хочу|дай|покажи) .*(рецепт|блюдо)",
            r"(выбрать?|беру|возьму|подходит|подойдёт)$",
        ],
        "weight": 1.9,
        "negative_keywords": ["что"],
    },
]


class Keyworder():
    def _get_names(self, addr):
        template = ScTemplate()
        template.quintuple(
            addr,
            sc_type.VAR_COMMON_ARC,
            sc_type.VAR_NODE_LINK >> '_name',
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes['nrel_main_idtf']
        )
        template2 = ScTemplate()
        template2.quintuple(
            addr,
            sc_type.VAR_COMMON_ARC,
            sc_type.VAR_NODE_LINK >> '_name',
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes['nrel_idtf']
        )
        names = [c.get_link_content(link.get('_name'))[0].data for link in c.search_by_template(template2)]
        names.append(c.get_link_content(c.search_by_template(template)[0].get('_name'))[0].data)
        return names
    
    def get_ingr_keys(self):
        concept_ingr = ScKeynodes['concept_ingredient']
        template = ScTemplate()
        template.quintuple(
            concept_ingr,
            sc_type.VAR_COMMON_ARC,
            sc_type.VAR_NODE >> '_ingr',
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes['nrel_inclusion']
        )
        result = {}
        for temp in c.search_by_template(template):
            result[get_element_system_identifier(temp.get('_ingr'))] = self._get_names(temp.get('_ingr'))
        return result

    def get_rec_keys(self):
        concept_ingr = ScKeynodes['concept_recipe']
        template = ScTemplate()
        template.triple(
            concept_ingr,
            sc_type.VAR_POS_ARC,
            sc_type.VAR_NODE >> '_rec',
        )
        result = {}
        for temp in c.search_by_template(template):
            result[get_element_system_identifier(temp.get('_rec'))] = self._get_names(temp.get('_rec'))
        return result

class MessageClassifier:
    def __init__(self):
        self.morph = pymorphy3.MorphAnalyzer()
        self.rules = RULES
        self.ingr_map = {}
        for key, value in Keyworder().get_ingr_keys().items():
            self.ingr_map[key] = [self.normalize(v) for v in value]
        self.rec_map = {}
        for key, value in Keyworder().get_rec_keys().items():
            self.rec_map[key] = [self.normalize(v) for v in value]

    def classify(self, text, user_ingredients=None, offered_ingredients=None, current_recipe_step=None):
        lemmas = self.tokenize(text)
        lemma_set = set(lemmas)
        original_text = " ".join(re.findall(r"[а-яёА-ЯЁ]+", text.lower()))

        best_category = CATEGORY_UNKNOWN
        best_score = 0.0

        for rule in self.rules:
            if self.rule_matches(rule, lemma_set, original_text):
                if rule["weight"] > best_score:
                    best_score = rule["weight"]
                    best_category = rule["category"]

        # if best_category == CATEGORY_UNKNOWN:
        #     best_category, best_score = self.contextual_rules(
        #         lemma_set, original_text, offered_ingredients, current_recipe_step)

        entities = self.extract_entities(original_text, best_category)
        return best_category, entities
    
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

    def rule_matches(self, rule, lemma_set, original_text):
        """Проверяет совпадение правила.
        
        - Одиночные keywords сравниваются с lemma_set (нормальные формы).
        - Многокомпонентные keywords и patterns сравниваются с original_text
          (исходный текст в нижнем регистре), чтобы корректно матчить
          словоформы вроде «мои ингредиенты», «покажи ингредиенты» и т.д.
        """
        negative = rule.get("negative_keywords", [])
        if negative and lemma_set & set(negative):
            return False

        keyword_hit = False
        for kw in rule["keywords"]:
            if " " in kw:
                if kw in original_text:
                    keyword_hit = True
                    break
            elif kw in lemma_set:
                keyword_hit = True
                break

        pattern_hit = False
        for pat in rule["patterns"]:
            if re.search(pat, original_text):
                pattern_hit = True
                break

        return keyword_hit or pattern_hit

    # def contextual_rules(self, lemma_set, original_text, offered_ingredients, current_recipe_step):
    #     # Проверка на упоминание конкретного рецепта
    #     for recipe_id, keywords in RECIPE_KEYWORDS.items():
    #         if lemma_set & set(keywords):
    #             return CATEGORY_SELECT_RECIPE, 2.0

    #     return CATEGORY_UNKNOWN, 0.0

    def extract_entities(self, text, category):
        entities = []
        normalized = self.normalize(text)

        if category in (
            CATEGORY_ADD_INGREDIENT,
            CATEGORY_DEL_INGREDIENT,
            CATEGORY_SEARCH_RECIPE,
        ):
            entities = self._map_to_ingredient_ids(normalized)

        if category == CATEGORY_SELECT_RECIPE:
            entities = self._map_to_recipe_ids(normalized)

        if category == CATEGORY_ALLERGY:
            entities = self._map_to_ingredient_ids(normalized)

        if category == CATEGORY_PREFERENCE:
            entities = self._map_to_ingredient_ids(normalized)

        if 'butter' in entities and 'vegetable_oil' in entities and not 'сливочный' in normalized:
            entities.remove('butter')
        return entities

    def _map_to_ingredient_ids(self, normalized):
        result = []
        for eng_id, patterns in self.ingr_map.items():
            for pattern in patterns:
                if pattern in normalized:
                    if eng_id not in result:
                        result.append(eng_id)

        return result

    def _map_to_recipe_ids(self, normalized):
        result = []
        for eng_id, patterns in self.rec_map.items():
            for pattern in patterns:
                if pattern in normalized:
                    if eng_id not in result:
                        result.append(eng_id)
        return result

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
