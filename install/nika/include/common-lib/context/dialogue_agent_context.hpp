#pragma once

#include "advanced_agent_context.hpp"

class Message;
class MessageDialogue;

/*!
 * @class DialogueAgentContext
 * @brief Extends AdvancedAgentContext with message and dialogue management utilities for dialogue systems.
 *
 * The DialogueAgentContext class provides specialized methods for working with messages and dialogues
 * in dialogue systems. It supports converting sc-addresses to Message objects,
 * generating new messages with content, and resolving or creating dialogues between participants.
 *
 * Features:
 * - Constructs from an existing sc-memory context or a user sc-address.
 * - Converts sc-addresses to Message objects for easy message manipulation.
 * - Generates new messages with specified text content.
 * - Resolves existing dialogues between two participants or creates a new dialogue if none exists.
 *
 * This class is designed for use in dialogue agents and reply production workflows,
 * where high-level abstractions over messages and dialogues are required.
 *
 * @note Inherits all advanced entity and user utilities from AdvancedAgentContext.
 *
 * @see AdvancedAgentContext
 * @see Message
 * @see MessageDialogue
 */
class DialogueAgentContext : public AdvancedAgentContext
{
public:
  /*!
   * @brief Default constructor, creates a new sc-memory context.
   */
  DialogueAgentContext() noexcept;

  /*!
   * @brief Constructs from an existing sc_memory_context pointer.
   * @param context Pointer to the existing sc-memory context.
   */
  DialogueAgentContext(sc_memory_context * context) noexcept;

  /*!
   * @brief Constructs context associated with a specific user.
   * @param userAddr sc-address of the user node.
   */
  DialogueAgentContext(ScAddr const & userAddr) noexcept;

  /*!
   * @brief Move constructor for efficient context transfer.
   */
  DialogueAgentContext(DialogueAgentContext && other) noexcept;

  /*!
   * @brief Move assignment operator.
   */
  DialogueAgentContext & operator=(DialogueAgentContext && other) noexcept;

  /*!
   * @brief Converts an sc-address to a Message object.
   * @param messageAddr sc-address of the message.
   * @return Message instance representing the given address.
   * @throws std::exception if the conversion is invalid.
   */
  Message ConvertToMessage(ScAddr const & messageAddr) noexcept(false);

  /*!
   * @brief Generates a new message with the specified text content and message class.
   * @param text The content of the new message.
   * @param messageClassAddr sc-address of the message class to use for the message.
   * @return Message instance representing the newly created message.
   * @throws std::exception if generation fails.
   */
  Message GenerateMessage(std::string const & text, ScAddr const & messageClassAddr = ScAddr::Empty) noexcept(false);

  /*!
   * @brief Resolves or creates a dialogue between two participants.
   *
   * Searches for an existing dialogue involving both participants; if none is found,
   * generates a new dialogue structure in the knowledge base.
   *
   * @param firstParticipantAddr sc-address of the first participant.
   * @param secondParticipantAddr sc-address of the second participant.
   * @return MessageDialogue instance representing the resolved or created dialogue.
   * @throws utils::ExceptionItemNotFound if the dialogue cannot be resolved or created.
   */
  MessageDialogue ResolveDialogueBetweenTwoParticipants(
      ScAddr const & firstParticipantAddr,
      ScAddr const & secondParticipantAddr) noexcept(false);
};
