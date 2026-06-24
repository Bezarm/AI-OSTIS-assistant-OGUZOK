from sc_kpm import ScKeynodes
from sc_kpm.sc_sets import ScOrientedSet
from sc_kpm.utils import get_element_system_identifier
from sc_client import client as c
from sc_client.constants import sc_type 
from sc_client.models import ScTemplate
import random
from pathlib import Path
from classifier import MessageClassifier
import re

class Operator():
    def __init__(self):
        self.userpath = Path(__file__).parent.parent/'knowledge_base'/'users'/'telegram'
        self.recpath = Path(__file__).parent.parent/'knowledge_base'/'oguzok'/'recipes'
        self.mc = MessageClassifier()
    
    def get_name(self, addr):
        template2 = ScTemplate()
        template2.quintuple(
            addr,
            sc_type.VAR_COMMON_ARC,
            sc_type.VAR_NODE_LINK >> '_name',
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes['nrel_main_idtf']
        )
        return c.get_link_content(c.search_by_template(template2)[0].get('_name'))[0].data

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

    def get_step(self, recipe: str, step: int):
        recipe = ScKeynodes[recipe]
        template = ScTemplate()
        template.quintuple(
            recipe,
            sc_type.VAR_COMMON_ARC,
            sc_type.VAR_NODE >> '_tuple',
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes['nrel_recipe_step']
        )
        tupl = c.search_by_template(template)[0].get('_tuple')
        steps = ScOrientedSet(set_node=tupl)
        is_f = step==1
        is_l = step==len(steps)
        return self._form_step(steps.elements_list[step-1]), is_f, is_l
    
    def _form_step(self, addr):
        template = ScTemplate()
        template.quintuple(
            addr,
            sc_type.VAR_COMMON_ARC,
            sc_type.VAR_NODE >> '_descr',
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes['nrel_recipe_step_description']
        )
        return f"<b>{self.get_name(addr)}</b>\n\n{c.get_link_content(c.search_by_template(template)[0].get('_descr'))[0].data}"

    def get_rec_pref(self, tg_id: int):
        user = ScKeynodes[str(tg_id)]
        template = ScTemplate()
        template.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            sc_type.VAR_NODE >> '_rec',
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes['nrel_liked_recipe']
        )
        return [get_element_system_identifier(rec.get('_rec')) for rec in c.search_by_template(template)]

    def add_rec_pref(self, tg_id: int, name: str, recipe: str):
        user = ScKeynodes[str(tg_id)]
        template = ScTemplate()
        template.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            sc_type.VAR_NODE >> '_rec',
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes['nrel_liked_recipe']
        )
        scs_recs = "=> nrel_liked_recipe:\n"
        for rec in c.search_by_template(template):
            scs_recs += f"  {get_element_system_identifier(rec.get('_rec'))};\n"
        template2 = ScTemplate()
        template2.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            ScKeynodes[recipe],
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes['nrel_liked_recipe']
        )
        c.generate_by_template(template2)
        scs_recs += f"  {recipe};;\n"
        scs = f"""{tg_id}
<- concept_user;
=> nrel_full_name:
    [{name}];
=> nrel_user_id:
    [{tg_id}];
{scs_recs}"""
        with open(self.userpath/f'{tg_id}.scs', 'w') as file:
            file.write(scs)
    
    def add_recipe(self, dct):
        ingrs=""
        for d in dct['ingrs']:
            ingrs+=f"""    {dct['sid']}_{d['name']}
    (*
        <- {d['name']};;
        => nrel_amount: [{d['amount']}];;
        => nrel_type_of_unit: [{d['unit']}] (* <- lang_ru;; *);;
    *);\n"""
        sl = ""
        steps = ""
        for i, d in enumerate(dct['steps']):
            sl+=f"   ..step{i+1};\n"
            steps+=f"""..step{i+1}
    <- concept_recipe_step;
    => nrel_main_idtf:
    [{d['title']}]
    (* <- lang_ru;; *);
    => nrel_recipe_step_description:
    [{d['description']}]
    (* <- lang_ru;; *);;\n\n"""
            
        scs = f"""{dct['sid']}

<- concept_recipe;

=> nrel_main_idtf:
    [{dct['name']}]
    (* <- lang_ru;; *);

=> nrel_time_of_cooking:
    [{dct['time']}]
    (* <- lang_ru;; *);

=> nrel_calorific_value:
    [{dct['calories']}]
    (* <- lang_ru;; *);

=> nrel_count_of_portions:
    [{dct['portions']}]
    (* <- lang_ru;; *);

=> nrel_dificulty_of_cooking:
    [{dct['difficulty']}]
    (* <- lang_ru;; *);

=> nrel_has_ingredient:
{ingrs}

=> nrel_recipe_step: <
{sl[:-2]}
>;;

{steps}"""
        c.generate_elements_by_scs([scs])
        with open(self.recpath/f'{dct['sid']}.scs', 'w') as file:
            file.write(scs)
        

    def handle_message(self, tg_id: int, name: str, message: str):
        clasif, entities = self.mc.classify(message)
        if clasif in (3,4,9) and not entities:
            return 0, self.unknown_message(), None
        match clasif:
            case 0:
                return 0, self.unknown_message(), None
            case 1:
                return 1, self.greetings(name), None
            case 2:
                return 2, self.skills(), None
            case 3:
                return 3, self.ingr_add(tg_id, entities), entities
            case 4:
                return 4, self.ingr_del(tg_id, entities), entities
            case 5:
                return 5, self.ingr_view(tg_id), None
            case 8:
                return 8, *self.search_by_ingrs(tg_id)
            case 9:
                return 9, self.recipe_select(entities), entities
            # case _:
            #     return str(clasif)
            
    def unknown_message(self):
        return "🤔 Извини, я пока не знаю, как на это ответить.\nПопробуй переформулировать вопрос или уточнить детали — я всегда готов помочь!"
    
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
        answer = "🤖 <b>Я могу:</b>\n\n"
        for skill in result:
            answer+=f"  ▸ {self.get_name(skill.get('_skill'))}\n"
        return answer

    def ingr_add(self, tg_id, entities):
        user = ScKeynodes[str(tg_id)]
        names = []
        is_rep = False
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
                if len(c.search_by_template(template)) > 0:
                    is_rep = True
                else:
                    c.generate_by_template(template)
                    names.append(self.get_name(ingr))
        if names:
            items = ', '.join(names)
            return f"✅ <b>Добавлено:</b> {items}"
        elif is_rep:
            return f"🤨 Кажется, это у вас уже есть."
        else:
            return self.unknown_message()


    def ingr_del(self, tg_id, entities):
        user = ScKeynodes[str(tg_id)]
        names = []
        is_o = False
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
                if len(c.search_by_template(template)) > 0:
                    c.erase_elements(c.search_by_template(template)[0].get('_has'))
                    names.append(self.get_name(ingr))
                else:
                    is_o = True
        if names:
            items = ', '.join(names)
            return f"🗑️ <b>Убрано:</b> {items}"
        elif is_o:
            return f"🤨 Кажется, этого у вас и не было."
        else:
            return self.unknown_message()
    
    def ingr_all_del(self, tg_id):
        names = []
        user = ScKeynodes[str(tg_id)]
        template = ScTemplate()
        template.quintuple(
            user,
            sc_type.VAR_COMMON_ARC >> '_has',
            sc_type.VAR_NODE >> '_ingr',
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes['nrel_has']
        )
        for ingr in c.search_by_template(template):
            c.erase_elements(ingr.get('_has'))
            names.append(self.get_name(ingr.get('_ingr')))
        if names:
            items = ', '.join(names)
            return f"🗑️ <b>Убрано:</b> {items}"
        else:
            return f"🗑️ У тебя и так ничего нет"

    def ingr_view(self, tg_id):
        user = ScKeynodes[str(tg_id)]
        template = ScTemplate()
        template.quintuple(
            user,
            sc_type.VAR_COMMON_ARC,
            sc_type.VAR_NODE >> '_ingr',
            sc_type.VAR_PERM_POS_ARC,
            ScKeynodes['nrel_has']
        )
        names = [self.get_name(temp.get('_ingr')) for temp in c.search_by_template(template)]
        if names:
            items = ', '.join(names)
            return f"🛒 <b>Твои ингредиенты:</b>\n{items}"
        else:
            return "📭 У тебя пока нет ингредиентов. Добавь их, написав, например: <i>\"Добавь картошку\"</i>"

    def recipe_select(self, entities):
        if not entities:
            return self.unknown_message()
        answer = ""
        for ent in entities:
            recipe = ScKeynodes.get(str(ent))
            if recipe.is_valid():
                name = self.get_name(recipe)
                answer += f"📖 <b>{name}</b>\n\n"
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
                    answer += f"⏱ <b>Время:</b> {c.get_link_content(res[0].get('_time'))[0].data}\n"
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
                    answer += f"🔥 <b>Калории:</b> {c.get_link_content(res2[0].get('_cal'))[0].data}\n"
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
                    answer += f"🍽 <b>Порции:</b> {c.get_link_content(res3[0].get('_portions'))[0].data}\n"
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
                    answer += f"📊 <b>Сложность:</b> {c.get_link_content(res4[0].get('_diff'))[0].data}\n\n"
                template_ingr = ScTemplate()
                template_ingr.quintuple(
                    recipe,
                    sc_type.VAR_COMMON_ARC,
                    sc_type.VAR_NODE >> '_ingr_inst',
                    sc_type.VAR_PERM_POS_ARC,
                    ScKeynodes['nrel_has_ingredient']
                )
                answer += f"📃 <b>Ингредиенты:</b>\n"
                for ringr in c.search_by_template(template_ingr):
                    template_ingr2 = ScTemplate()
                    template_ingr2.quintuple(
                        ringr.get('_ingr_inst'),
                        sc_type.VAR_COMMON_ARC,
                        sc_type.VAR_NODE_LINK >> '_amount',
                        sc_type.VAR_PERM_POS_ARC,
                        ScKeynodes['nrel_amount']
                    )
                    amount = c.get_link_content(c.search_by_template(template_ingr2)[0].get('_amount'))[0].data
                    template_ingr3 = ScTemplate()
                    template_ingr3.quintuple(
                        ringr.get('_ingr_inst'),
                        sc_type.VAR_COMMON_ARC,
                        sc_type.VAR_NODE_LINK >> '_unit',
                        sc_type.VAR_PERM_POS_ARC,
                        ScKeynodes['nrel_type_of_unit']
                    )
                    unit = c.get_link_content(c.search_by_template(template_ingr3)[0].get('_unit'))[0].data
                    template_concept = ScTemplate()
                    template_concept.triple(
                        sc_type.VAR_NODE >> '_ingr',
                        sc_type.VAR_POS_ARC,
                        ringr.get('_ingr_inst'),
                    )
                    name = self.get_name(c.search_by_template(template_concept)[0].get('_ingr'))
                    answer += f"🔷 {name}: <i>{amount} {unit}</i>\n"
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
        user_ingr_addrs = set(t.get('_ingr') for t in c.search_by_template(template))
        if not user_ingr_addrs:
            return "📭 У тебя пока нет ингредиентов. Добавь их, написав, например: <i>\"Добавь яйца\"</i>", []

        concept_recipe = ScKeynodes['concept_recipe']
        template_rec = ScTemplate()
        template_rec.triple(
            concept_recipe,
            sc_type.VAR_POS_ARC,
            sc_type.VAR_NODE >> '_recipe',
        )
        all_recipes = [t.get('_recipe') for t in c.search_by_template(template_rec)]

        matching_recipes = []
        for recipe in all_recipes:
            template_ingr = ScTemplate()
            template_ingr.quintuple(
                recipe,
                sc_type.VAR_COMMON_ARC,
                sc_type.VAR_NODE >> '_ingr_inst',
                sc_type.VAR_PERM_POS_ARC,
                ScKeynodes['nrel_has_ingredient']
            )
            ingr_instances = [t.get('_ingr_inst') for t in c.search_by_template(template_ingr)]
            if not ingr_instances:
                continue

            all_covered = True
            for inst in ingr_instances:
                template_concept = ScTemplate()
                template_concept.triple(
                    sc_type.VAR_NODE >> '_concept',
                    sc_type.VAR_POS_ARC,
                    inst,
                )
                concepts = [t.get('_concept') for t in c.search_by_template(template_concept)]
                if not any(concept in user_ingr_addrs for concept in concepts):
                    all_covered = False
                    break

            if all_covered:
                matching_recipes.append(recipe)

        if not matching_recipes:
            return "😔 К сожалению, по твоим ингредиентам ничего не нашлось.\nПопробуй добавить ещё продуктов!", []

        answer = "🔍 <b>Найденные рецепты:</b>\n\n"
        names = []
        for recipe in matching_recipes:
            names.append(self.get_name(recipe))
            answer += f"  ◆ <b>{self.get_name(recipe)}</b>\n"
        return answer, names

class Connector():
    def safe_connect(self, url):
        if not c.is_connected():
            c.connect(url)
    
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
    