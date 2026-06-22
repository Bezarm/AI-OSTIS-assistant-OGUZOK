from sc_kpm import ScKeynodes
from sc_client import client as c
from sc_client.constants import sc_type 
from sc_client.models import (ScAddr, ScLinkContent, ScConstruction, 
                            ScLinkContentType, ScTemplate,
                            ScEventSubscriptionParams)
from sc_client.constants.common import ScEventType
import random
from pathlib import Path
from classifier import MessageClassifier

class Operator():
    def __init__(self):
        self.userpath = Path(__file__).parent.parent/'knowledge_base'/'users'/'telegram'
    
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
        clasif, entities = MessageClassifier().classify(message)
        match clasif:
            case 0:
                return self.unknown_message()
            case 1:
                return self.greetings(name)
            case 2:
                return self.skills()
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
    