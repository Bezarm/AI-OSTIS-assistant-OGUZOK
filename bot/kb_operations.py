from sc_kpm import ScKeynodes
from sc_kpm.utils import get_element_system_identifier
from sc_client import client as c
from sc_client.constants import sc_type 
from sc_client.models import (ScAddr, ScLinkContent, ScConstruction, 
                            ScLinkContentType, ScTemplate,
                            ScEventSubscriptionParams)
from sc_client.constants.common import ScEventType
from pathlib import Path
import asyncio

class Operator():
    def __init__(self):
        self.userpath = Path(__file__).parent.parent/'knowledge_baze'/'users'/'telegram'
    
    def add_user(self, tg_id, name):
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
    
    def add_message(self, tg_id, text):
        user = ScKeynodes[str(tg_id)]
        bound = ScKeynodes['nrel_message_author']
        construction = ScConstruction()
        construction.generate_link(sc_type.CONST_NODE_LINK, ScLinkContent(text, ScLinkContentType.STRING), '_message')
        message_addr = c.generate_elements(construction)
        template = ScTemplate()
        template.quintuple(
            message_addr[0],
            sc_type.VAR_COMMON_ARC,
            user,
            sc_type.VAR_PERM_POS_ARC,
            bound
        )
        c.generate_by_template(template)
        

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
    
    def subscribe_to_message(self, message_sender) -> list:
        keynode_nrel_reply_to_message = ScKeynodes['nrel_reply_to_message']

        def on_message_replied(subscribed_addr: ScAddr, arc: ScAddr,
                               message_to_reply_message_arc_addr: ScAddr):
            reply_message_alias = '_reply_message'
            template = ScTemplate()
            template.triple(
                sc_type.VAR_NODE_LINK >> reply_message_alias,
                message_to_reply_message_arc_addr,
                sc_type.VAR_NODE_LINK
            )
            result = c.search_by_template(template)
            if not result:
                return 
            reply_message_addr = result[0].get(reply_message_alias)
            print(reply_message_addr)
            # # template.triple(
            # #     result[0].addrs[2],
            # #     ScKeynodes['nrel_message_author'],
            # #     sc_type.CONST_NODE
            # # )
            # result2 = c.search_by_template(result[0].addrs[2])
            # print(result2)
            # 2. Ищем автора reply-сообщения через quintuple
            #    Структура: reply_msg --(common_arc)--> author
            #              nrel_message_author --(perm_pos_arc)--> common_arc
            author_alias = '_author'
            template2 = ScTemplate()
            template2.quintuple(
                result[0].addrs[2],
                sc_type.VAR_COMMON_ARC,
                sc_type.VAR_NODE >> author_alias,
                sc_type.VAR_PERM_POS_ARC,
                ScKeynodes['nrel_message_author']
            )
            result2 = c.search_by_template(template2)
            if not result2:
                return
            author_addr = result2[0].get(author_alias)
            print(author_addr)
        
            # 3. Ищем tg_id у автора
            #    Структура: author --(common_arc)--> [tg_id_link]
            #              nrel_user_id --(perm_pos_arc)--> common_arc
            # tg_id_alias = '_tg_id'
            # template3 = ScTemplate()
            # template3.quintuple(
            #     author_addr,
            #     sc_type.VAR_COMMON_ARC,
            #     sc_type.VAR_NODE_LINK >> tg_id_alias,
            #     sc_type.VAR_PERM_POS_ARC,
            #     ScKeynodes['nrel_user_id']
            # )
            # result3 = c.search_by_template(template3)
            # if not result3:
            #     return
            # tg_id_link = result3[0].get(tg_id_alias)
            # print(tg_id_link)
            # tg_id = c.get_link_content(tg_id_link)[0].data
            tg_id = get_element_system_identifier(author_addr)
            text = c.get_link_content(reply_message_addr)[0].data
            message_sender(int(tg_id), text)

        event_params = ScEventSubscriptionParams(keynode_nrel_reply_to_message, 
                                                    ScEventType.AFTER_GENERATE_OUTGOING_ARC, on_message_replied)
        return c.create_elementary_event_subscriptions(event_params)
    