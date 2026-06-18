from sc_kpm import ScKeynodes
from sc_client.client import (connect, disconnect, is_connected,
                              generate_elements, generate_by_template,
                              search_links_by_contents, search_by_template, 
                              create_elementary_event_subscriptions, get_link_content, generate_elements_by_scs)
from sc_client.constants import sc_type 
from sc_client.models import (SCs, ScAddr, ScLinkContent, ScConstruction, 
                            ScLinkContentType, ScTemplate,
                            ScEventSubscriptionParams)
from pathlib import Path

class Operator():
    def __init__(self):
        self.userpath = Path(__file__).parent.parent/'knowledge-base'/'users'/'telegram'
    
    def add_user(self, tg_id):
        if not ScKeynodes[str(tg_id)].is_valid():
            scs = f"""{tg_id}
<- concept_user;
=> nrel_user_id:
    [{tg_id}];;
"""
            generate_elements_by_scs([scs])
            with open(self.userpath/f'{tg_id}.scs', 'w') as file:
                file.write(scs)
    
    def add_message(self, tg_id, text):
        user = ScKeynodes[str(tg_id)]
        bound = ScKeynodes['nrel_message_author']
        construction = ScConstruction()
        construction.generate_link(sc_type.CONST_NODE_LINK, ScLinkContent(text, ScLinkContentType.STRING), '_message')
        message_addr = generate_elements(construction)
        template = ScTemplate()
        template.quintuple(
            message_addr[0],
            sc_type.VAR_COMMON_ARC,
            user,
            sc_type.VAR_PERM_POS_ARC,
            bound
        )
        result = generate_by_template(template)
        

class Connector():
    def safe_connect(self, url):
        if not is_connected():
            connect(url)
    def __del__(self):
        disconnect()
    