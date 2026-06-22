from sc_kpm import ScKeynodes
from sc_client import client as c
from sc_client.constants import sc_type 
from sc_client.models import ScTemplate
import random
from pathlib import Path
from classifier import MessageClassifier

class Operator():
    def __init__(self):
        self.userpath = Path(__file__).parent.parent/'knowledge_base'/'users'/'telegram'
        self.mc = MessageClassifier()
    
    def add_user(self, tg_id: int, name: str):
        if not ScKeynodes.get(str(tg_id)).is_valid():
            scs = f"""{tg_id}
<- concept_user;
=> nrel_full_name:
    [{name}];
=> nrel_user_id:
    [{tg_id}];;
"""
            c.generate_elements_by_scs([scs])
            with open(self.userpath/f'{tg_id}.scs', 'w') as file:
                file.write(scs)
    
    # def add_message(self, tg_id, text):
    #     user = ScKeynodes[str(tg_id)]
    #     bound = ScKeynodes['nrel_message_author']
    #     construction = ScConstruction()
    #     construction.generate_link(sc_type.CONST_NODE_LINK, ScLinkContent(text, ScLinkContentType.STRING), '_message')
    #     message_addr = c.generate_elements(construction)
    #     template = ScTemplate()
    #     template.quintuple(
    #         message_addr[0],
    #         sc_type.VAR_COMMON_ARC,
    #         user,
    #         sc_type.VAR_PERM_POS_ARC,
    #         bound
    #     )
    #     c.generate_by_template(template)

    def handle_message(self, tg_id: int, name: str, message: str):
        clasif, entities = self.mc.classify(message)
        match clasif:
            case 0:
                return self.unknown_message()
            case 1:
                return self.greetings(name)
            case 2:
                return self.skills()
            case 3:
                return self.ingr_add(tg_id,entities)
            case 4:
                return self.ingr_del(tg_id,entities)
            case 5:
                return self.ingr_view(tg_id)
            # case 8:
            #     return self.search_by_ingrs(tg_id)
            # case 9:
            #     return self.recipe_select(entities)
            case _:
                return str(clasif)
            
    def unknown_message(self):
        return """Извини, я пока не знаю, как на это ответить.
Попробуй переформулировать вопрос или уточнить детали — я всегда готов помочь!"""
    
    def greetings(self, name):
        answers = [f"""Привет, {name}! 😊

Как твои дела? Я в отличном настроении и готов помочь 🚀

Спрашивай, что угодно, или набери "Что ты умеешь", чтобы узнать, чем я могу тебе помочь! 😀""", f"""Я тебя вижу, {name}! 🤖

Я только что узнал новый рецепт и уже хочу свернуть горы. 🏔️

Если интересно, чем я могу помочь, напиши "Что ты умеешь" 😄"""]
        return random.choice(answers)
    
    def skills(self):
        myself = ScKeynodes['myself']
        template = ScTemplate()
        template.quintuple(
            myself,
            sc_type.VAR_COMMON_ARC,
            sc_type.VAR_NODE >> '_skill',
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes['nrel_skills']
        )
        result = c.search_by_template(template)
        answer = "Я могу:\n"
        for skill in result:
            template2 = ScTemplate()
            template2.quintuple(
                skill.get('_skill'),
                sc_type.VAR_COMMON_ARC,
                sc_type.VAR_NODE_LINK >> '_skill_text',
                sc_type.VAR_PERM_POS_ARC,
                ScKeynodes['nrel_main_idtf']
            )
            answer+=f"▪ {c.get_link_content(c.search_by_template(template2)[0].get('_skill_text'))[0].data}\n"
        return answer
    
    def _get_ingr_name(self, ingr):
        template2 = ScTemplate()
        template2.quintuple(
            ingr,
            sc_type.VAR_COMMON_ARC,
            sc_type.VAR_NODE_LINK >> '_name',
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes['nrel_main_idtf']
        )
        return c.get_link_content(c.search_by_template(template2)[0].get('_name'))[0].data

    def ingr_add(self, tg_id, entities):
        user = ScKeynodes[str(tg_id)]
        answer = "Я добавил эти ингредиенты: "
        for ent in entities:
            ingr = ScKeynodes.get(str(ent))
            if ingr.is_valid():
                template = ScTemplate()
                template.quintuple(
                    user,
                    sc_type.VAR_COMMON_ARC,
                    ingr,
                    sc_type.VAR_PERM_POS_ARC,
                    ScKeynodes['nrel_has']
                )
                c.generate_by_template(template)
                answer += f"{self._get_ingr_name(ingr)}, "
        if answer!="Я добавил эти ингредиенты: ":
            return answer[:-2]+"."
        else:
            return self.unknown_message()


    def ingr_del(self, tg_id, entities):
        user = ScKeynodes[str(tg_id)]
        answer = "Я убрал эти ингредиентам: "
        for ent in entities:
            ingr = ScKeynodes.get(str(ent))
            if ingr.is_valid():
                template = ScTemplate()
                template.quintuple(
                    user,
                    sc_type.VAR_COMMON_ARC >> '_has',
                    ingr,
                    sc_type.VAR_PERM_POS_ARC,
                    ScKeynodes['nrel_has']
                )
                c.erase_elements(c.search_by_template(template)[0].get('_has'))
                answer += f"{self._get_ingr_name(ingr)}, "
        if answer!="Я убрал эти ингредиентам: ":
            return answer[:-2]+"."
        else:
            return self.unknown_message()

    def ingr_view(self, tg_id):
        user = ScKeynodes[str(tg_id)]
        answer = "Мы ищем по этим ингредиентам: "
        template = ScTemplate()
        template.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            sc_type.VAR_NODE >> '_ingr',
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes['nrel_has']
        )
        for temp in c.search_by_template(template):
            answer += f"{self._get_ingr_name(temp.get('_ingr'))}, "
        if answer!="Мы ищем по этим ингредиентам: ":
            return answer[:-2]+"."
        else:
            return "Я пока не знаю какие ингредиенты у тебя есть."

    def _get_recipe_name(self, recipe):
        template2 = ScTemplate()
        template2.quintuple(
            sc_type.VAR_NODE_LINK >> '_name',
            sc_type.VAR_COMMON_ARC,
            recipe,
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes['nrel_main_idtf']
        )
        result = c.search_by_template(template2)
        if result:
            return c.get_link_content(result[0].get('_name'))[0].data
        return str(recipe)

    def recipe_select(self, entities):
        """Показывает информацию о конкретном рецепте по его English scs id."""
        if not entities:
            return self.unknown_message()
        answer = ""
        for ent in entities:
            recipe = ScKeynodes.get(str(ent))
            if recipe.is_valid():
                name = self._get_recipe_name(recipe)
                answer += f"📖 {name}\n\n"
                # Время приготовления
                template = ScTemplate()
                template.quintuple(
                    recipe,
                    sc_type.VAR_COMMON_ARC,
                    sc_type.VAR_NODE_LINK >> '_time',
                    sc_type.VAR_PERM_POS_ARC,
                    ScKeynodes['nrel_time_of_cooking']
                )
                res = c.search_by_template(template)
                if res:
                    answer += f"⏱ Время: {c.get_link_content(res[0].get('_time'))[0].data}\n"
                # Калорийность
                template2 = ScTemplate()
                template2.quintuple(
                    recipe,
                    sc_type.VAR_COMMON_ARC,
                    sc_type.VAR_NODE_LINK >> '_cal',
                    sc_type.VAR_PERM_POS_ARC,
                    ScKeynodes['nrel_calorific_value']
                )
                res2 = c.search_by_template(template2)
                if res2:
                    answer += f"🔥 Калории: {c.get_link_content(res2[0].get('_cal'))[0].data}\n"
                # Порции
                template3 = ScTemplate()
                template3.quintuple(
                    recipe,
                    sc_type.VAR_COMMON_ARC,
                    sc_type.VAR_NODE_LINK >> '_portions',
                    sc_type.VAR_PERM_POS_ARC,
                    ScKeynodes['nrel_count_of_portions']
                )
                res3 = c.search_by_template(template3)
                if res3:
                    answer += f"🍽 Порции: {c.get_link_content(res3[0].get('_portions'))[0].data}\n"
                # Сложность
                template4 = ScTemplate()
                template4.quintuple(
                    recipe,
                    sc_type.VAR_COMMON_ARC,
                    sc_type.VAR_NODE_LINK >> '_diff',
                    sc_type.VAR_PERM_POS_ARC,
                    ScKeynodes['nrel_dificulty_of_cooking']
                )
                res4 = c.search_by_template(template4)
                if res4:
                    answer += f"📊 Сложность: {c.get_link_content(res4[0].get('_diff'))[0].data}\n"
                answer += "\n"
        if answer:
            return answer.strip()
        else:
            return self.unknown_message()

    def search_by_ingrs(self, tg_id):
        user = ScKeynodes[str(tg_id)]
        template = ScTemplate()
        template.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            sc_type.VAR_NODE >> '_ingr',
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes['nrel_has']
        )
        user_ingrs = [t.get('_ingr') for t in c.search_by_template(template)]
        if not user_ingrs:
            return "У тебя пока нет ингредиентов. Добавь их сначала!"
        recipes = set()
        for ingr in user_ingrs:
            template2 = ScTemplate()
            template2.quintuple(
                sc_type.VAR_NODE >> '_recipe',
                sc_type.VAR_COMMON_ARC,
                ingr,
                sc_type.VAR_PERM_POS_ARC,
                ScKeynodes['nrel_has_ingredient']
            )
            for rec in c.search_by_template(template2):
                recipes.add(rec.get('_recipe'))
        if not recipes:
            return "К сожалению, по твоим ингредиентам ничего не нашлось."
        answer = "Найденные рецепты:\n"
        for recipe in recipes:
            answer += f"\u25AA {self._get_recipe_name(recipe)}\n"
        return answer

class Connector():
    def safe_connect(self, url):
        if not c.is_connected():
            c.connect(url)
        
            c.set_reconnect_handler(
                reconnect_handler=c.connect,
                post_reconnect_handler=None,
                reconnect_retries=5,
                reconnect_retry_delay=1.0
            )
    
    def __del__(self):
        c.disconnect()
    
    # def subscribe_to_message(self, message_sender) -> list:
    #     keynode_nrel_reply_to_message = ScKeynodes['nrel_reply_to_message']

    #     def on_message_replied(subscribed_addr: ScAddr, arc: ScAddr,
    #                            message_to_reply_message_arc_addr: ScAddr):
    #         template = ScTemplate()
    #         template.triple(
    #             sc_type.VAR_NODE_LINK >> '_reply_message',
    #             message_to_reply_message_arc_addr,
    #             sc_type.VAR_NODE_LINK
    #         )
    #         result = c.search_by_template(template)
    #         if not result:
    #             return 
    #         reply_message_addr = result[0].get('_reply_message')

    #         template2 = ScTemplate()
    #         template2.quintuple(
    #             result[0].addrs[2],
    #             sc_type.VAR_COMMON_ARC,
    #             sc_type.VAR_NODE >> '_author',
    #             sc_type.VAR_PERM_POS_ARC,
    #             ScKeynodes['nrel_message_author']
    #         )
    #         result2 = c.search_by_template(template2)
    #         if not result2:
    #             return
    #         author_addr = result2[0].get('_author')
        
    #         template3 = ScTemplate()
    #         template3.quintuple(
    #             author_addr,
    #             sc_type.VAR_COMMON_ARC,
    #             sc_type.VAR_NODE_LINK >> '_tg_id',
    #             sc_type.VAR_PERM_POS_ARC,
    #             ScKeynodes['nrel_user_id']
    #         )
    #         result3 = c.search_by_template(template3)
    #         if not result3:
    #             return
    #         tg_id_link = result3[0].get('_tg_id')
    #         tg_id = c.get_link_content(tg_id_link)[0].data
    #         text = c.get_link_content(reply_message_addr)[0].data
    #         message_sender(int(tg_id), text, parse_mode='HTML')

    #     event_params = ScEventSubscriptionParams(keynode_nrel_reply_to_message, 
    #                                                 ScEventType.AFTER_GENERATE_OUTGOING_ARC, on_message_replied)
    #     return c.create_elementary_event_subscriptions(event_params)
    