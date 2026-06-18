#pragma once

#include <sc-memory/sc_addr.hpp>

class DialogueAgentContext;
class ScSet;
class MessageDialogue;

/*!
 * @class Message
 * @brief Represents a message in a dialogue system, providing high-level message manipulation and query operations.
 *
 * The Message class encapsulates a message node in sc-memory, offering methods to access and modify message content,
 * metadata, and relationships. It integrates with DialogueAgentContext for context-aware operations and supports
 * retrieval of message text, topic class, recognized entity classes, author information, and dialogue context.
 * It also enables setting the message author and reply message, and manages message-dialogue associations.
 *
 * Features:
 * - Constructs from a DialogueAgentContext and message sc-address.
 * - Retrieves and sets the message text.
 * - Retrieves and sets the message topic class (intent).
 * - Retrieves and sets recognized entity classes for the message.
 * - Sets not recognized entity classes for the message.
 * - Sets not expected recognized entity classes for the message.
 * - Retrieves and sets the message author.
 * - Retrieves the author’s class and author message class.
 * - Retrieves the dialogue containing the message.
 * - Sets a reply message, linking it to the original message and adding it to the dialogue.
 *
 * This class is typically used in dialogue agents, reply production, and message processing workflows.
 *
 * @note This class is intended for internal use within dialogue and message handling subsystems.
 *
 * @see DialogueAgentContext
 * @see MessageDialogue
 * @see ScAddr
 */
class Message : public ScAddr
{
public:
  friend class DialogueAgentContext;

  /*!
   * @brief Default constructor.
   */
  Message();

  /*!
   * @brief Destructor.
   */
  ~Message();

  /*!
   * @brief Retrieves the message text content.
   * @return The message text as a string.
   */
  std::string GetText() const;

  /*!
   * @brief Sets the message text content.
   * @param text The new message text.
   */
  void SetText(std::string const & text);

  /*!
   * @brief Retrieves the topic class (intent) of the message.
   * @return sc-address of the topic class.
   * @throws utils::ExceptionItemNotFound if the topic class is not found.
   */
  ScAddr GetTopicClass() const;

  /*!
   * @brief Sets the topic class (intent) of the message.
   * @param topicClassAddr sc-address of the new topic class.
   */
  void SetTopicClass(ScAddr const & topicClassAddr);

  /*!
   * @brief Retrieves the set of recognized entity classes for the message.
   * @return ScSet containing recognized entity classes.
   * @throws utils::ExceptionItemNotFound if no recognized entity classes are found.
   */
  ScSet GetRecognizedEntityClasses() const;

  /*!
   * @brief Sets the recognized entity classes for the message.
   * @param entityClassesArcs Set of sc-addresses for entity classes.
   */
  void SetRecognizedEntityClasses(ScAddrToValueUnorderedMap<ScAddr> const & entityClassesArcs);

  /*!
   * @brief Sets the not recognized entity classes for the message.
   * @param entityClasses Set of sc-addresses for not recognized entity classes.
   */
  void SetNotRecognizedEntityClasses(ScAddrUnorderedSet const & entityClasses);

  /*!
   * @brief Sets the not expected recognized entity classes for the message.
   * @param entityClasses Set of sc-addresses for not expected recognized entity classes.
   */
  void SetNotExpectedRecognizedEntityClasses(ScAddrUnorderedSet const & entityClasses);

  /*!
   * @brief Retrieves the author of the message.
   * @return sc-address of the author.
   * @throws utils::ExceptionItemNotFound if the author is not found.
   */
  ScAddr GetAuthor() const;

  /*!
   * @brief Sets the author of the message.
   * @param authorAddr sc-address of the author.
   */
  void SetAuthor(ScAddr const & authorAddr);

  /*!
   * @brief Retrieves the class of the message author.
   * @return sc-address of the author's class.
   * @throws utils::ExceptionItemNotFound if the author class is not found.
   */
  ScAddr GetAuthorClass() const;

  /*!
   * @brief Retrieves the author message class (specific message class for the author).
   * @return sc-address of the author message class.
   * @throws utils::ExceptionItemNotFound if the author message class is not found.
   */
  ScAddr GetAuthorMessageClass() const;

  /*!
   * @brief Retrieves the dialogue containing the message.
   * @return MessageDialogue instance representing the dialogue.
   * @throws utils::ExceptionItemNotFound if the dialogue is not found.
   */
  MessageDialogue GetDialogue() const;

  /*!
   * @brief Sets a reply message, linking it to this message and adding it to the dialogue.
   * @param replyMessage The reply message to set.
   */
  void SetReplyMessage(Message const & replyMessage);

  /*!
   * @brief Retrieves the set of expected user reply message classes for the message.
   * @return ScSet containing expected user reply message classes.
   * @throws utils::ExceptionItemNotFound if no expected user reply message classes are found.
   */
  ScSet GetExpectedUserReplyMessageClasses() const;

  /*!
   * @brief Sets the set of expected user reply message classes for the message.
   *
   * @param expectedUserReplyMessageClasses Set of sc-addresses for expected user reply message
   * classes.
   */
  void SetExpectedUserReplyMessageClasses(ScAddrUnorderedSet const & expectedUserReplyMessageClasses);

  /*!
   * @brief Retrieves the immediate previous message in the dialogue sequence from the specified author.
   *
   * Searches the current dialogue structure for all messages in the basic sequence chain.
   * For each message linked as predecessor via nrel_basic_sequence, it checks if the author
   * matches the specified author, and returns the first such message found.
   *
   * If no valid previous message from the specified author is found, returns an invalid Message object.
   * If the arc from the dialogue object to this message cannot be found, throws ExceptionItemNotFound.
   *
   * This method is used to locate contextual prior messages from the same participant, which may
   * be important for context-based entity extraction or flow tracking within a dialogue.
   *
   * @return Message The previous message from the specified author in the dialogue sequence, or invalid Message if none
   * found.
   * @throws utils::ExceptionItemNotFound If the arc from the dialogue to this message is missing.
   */
  Message GetPreviousMessageWithAuthor(ScAddr const & authorAddr) const;

protected:
  DialogueAgentContext * m_context;  ///< Pointer to the dialogue agent context.

  /*!
   * @brief Constructs a Message instance.
   * @param context Pointer to the DialogueAgentContext.
   * @param messageAddr sc-address of the message node.
   */
  Message(DialogueAgentContext * context, ScAddr const & messageAddr);
};
