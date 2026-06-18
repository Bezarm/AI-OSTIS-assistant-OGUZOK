#pragma once

#include <sc-memory/sc_oriented_set.hpp>

class User;
class DialogueAgentContext;

/*!
 * @class MessageDialogue
 * @brief Represents a dialogue between two participants in sc-memory, with message history and participant management.
 *
 * The MessageDialogue class encapsulates the logic for managing dialogues in systems.
 * It provides methods to retrieve the participants of a dialogue and to get the other participant given one,
 * facilitating easy navigation and manipulation of dialogue structures.
 *
 * Features:
 * - Constructs from a DialogueAgentContext and a dialogue sc-address.
 * - Retrieves the sc-addresses of both dialogue participants.
 * - Returns the other participant as a User object given one participant.
 * - Integrates with the DialogueAgentContext for user conversion and context-aware operations.
 *
 * This class is typically used in dialogue agents and message processing workflows to manage and query
 * dialogue participants and their relationships.
 *
 * @note This class is intended for internal use within dialogue and message handling subsystems.
 *
 * @see DialogueAgentContext
 * @see User
 * @see ScOrientedSet
 */
class MessageDialogue : public ScOrientedSet
{
public:
  friend class DialogueAgentContext;
  friend class Message;

  /*!
   * @brief Destructor.
   */
  ~MessageDialogue();

  /*!
   * @brief Retrieves the sc-addresses of both dialogue participants.
   * @return Tuple of sc-addresses representing the two participants.
   * @throws utils::ExceptionInvalidState if the participants cannot be found or if there are not exactly two.
   */
  std::tuple<ScAddr, ScAddr> GetParticipants() const;

  /*!
   * @brief Returns the other participant in the dialogue as a User object.
   * @param participant sc-address of one participant.
   * @return User object representing the other participant.
   * @throws utils::ExceptionInvalidState if the provided participant is not part of the dialogue.
   */
  User GetOtherParticipant(ScAddr const & participant) const;

protected:
  DialogueAgentContext * m_dialogueContext;  ///< Pointer to the dialogue agent context.

  /*!
   * @brief Constructs a MessageDialogue instance.
   * @param context Pointer to the DialogueAgentContext.
   * @param dialogueAddr sc-address of the dialogue node.
   */
  MessageDialogue(DialogueAgentContext * context, ScAddr const & dialogueAddr);
};
