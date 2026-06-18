#pragma once

#include <sc-memory/sc_keynodes.hpp>

class CommonKeynodes : public ScKeynodes
{
public:
  static inline ScKeynode const concept_dialogue{"concept_dialogue", ScType::ConstNodeClass};
  static inline ScKeynode const concept_message_topic{"concept_message_topic", ScType::ConstNodeClass};
  static inline ScKeynode const concept_message_classified_by_topic{
      "concept_message_classified_by_topic",
      ScType::ConstNodeClass};
  static inline ScKeynode const concept_user_class{"concept_user_class", ScType::ConstNodeClass};
  static inline ScKeynode const concept_link{"concept_link", ScType::ConstNodeClass};

  static inline ScKeynode const rrel_last{"rrel_last", ScType::ConstNodeRole};

  static inline ScKeynode const nrel_dialogue_participants{"nrel_dialogue_participants", ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_recognized_entity_classes{
      "nrel_recognized_entity_classes",
      ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_not_recognized_entity_classes{
      "nrel_not_recognized_entity_classes",
      ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_not_expected_recognized_entity_classes{
      "nrel_not_expected_recognized_entity_classes",
      ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_expected_user_reply_message_classes{
      "nrel_expected_user_reply_message_classes",
      ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_expected_user_negative_reply_message_classes{
      "nrel_expected_user_negative_reply_message_classes",
      ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_message_author{"nrel_message_author", ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_author_message_class{"nrel_author_message_class", ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_user_id{"nrel_user_id", ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_reply_to_message{"nrel_reply_to_message", ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_abbreviation{"nrel_abbreviation", ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_url{"nrel_url", ScType::ConstNodeNonRole};
  static inline ScKeynode const nrel_name{"nrel_name", ScType::ConstNodeNonRole};
};
