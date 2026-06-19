#pragma once

#include <optional>

#include <sc-memory/sc_agent_context.hpp>

class User;

/*!
 * @class AdvancedAgentContext
 * @brief Extended sc-agent context with advanced entity and user-related utilities.
 *
 * The AdvancedAgentContext class extends the base ScAgentContext providing additional high-level functionality
 * for handling users and entities commonly needed in dialogue and intelligent agent scenarios.
 * It facilitates conversion between sc-addresses and user objects, entity searching and resolution by main identifiers,
 * and retrieval of entity associated text content.
 *
 * Key features:
 * - Construction from existing sc-memory context or a user sc-address.
 * - Setting a logger for detailed debug information.
 * - Conversion from sc-address to User object.
 * - Searching entities by their main identifier text.
 * - Resolving entities by main identifier and class, with link content management.
 * - Extracting textual representation from entities, including link content and main identifiers.
 *
 * This class forms a foundation for advanced dialogue agents and knowledge-processing components,
 * providing convenient abstractions over low-level sc-memory operations.
 *
 * @note The class maintains its own ScLogger instance for internal logging.
 *
 * @see ScAgentContext
 * @see User
 */
class AdvancedAgentContext : public ScAgentContext
{
public:
  /*!
   * @brief Default constructor, creates a new sc-memory context.
   */
  AdvancedAgentContext() noexcept;

  /*!
   * @brief Constructs from an existing sc_memory_context pointer.
   * @param context Pointer to the existing sc-memory context.
   */
  AdvancedAgentContext(sc_memory_context * context) noexcept;

  /*!
   * @brief Constructs context associated with a specific user.
   * @param userAddr sc-address of the user node.
   */
  AdvancedAgentContext(ScAddr const & userAddr) noexcept;

  /*!
   * @brief Move constructor for efficient context transfer.
   */
  AdvancedAgentContext(AdvancedAgentContext && other) noexcept;

  /*!
   * @brief Move assignment operator.
   */
  AdvancedAgentContext & operator=(AdvancedAgentContext && other) noexcept;

  /*!
   * @brief Sets the logger for internal debugging and tracing.
   * @param logger Reference to an external ScLogger instance.
   */
  void SetLogger(utils::ScLogger & logger);

  /*!
   * @brief Converts an sc-address to a User object.
   * @param userAddr sc-address of the user.
   * @return User instance representing the given address.
   * @throws std::exception if the conversion is invalid.
   */
  User ConvertToUser(ScAddr const & userAddr) noexcept(false);

  /*!
   * @brief Searches for an entity node by its main or non-main identifier.
   * @param text The main or non-main identifier string to search for.
   * @return sc-address of the found entity or empty address if none found.
   */
  ScAddr SearchEntityByIdentifier(std::string const & text);

  /*!
   * @brief Resolves an entity by specified text and entity class.
   *
   * If the entity class represents a link type, attempts to find a link with the matching content;
   * otherwise, falls back to searching by main identifier. If missing, generates a new link entity.
   *
   * @param text The main identifier text.
   * @param entityClassAddr sc-address of the entity class.
   * @return sc-address of the resolved or newly created entity.
   */
  ScAddr ResolveEntityByTextAndClass(std::string const & text, ScAddr const & entityClassAddr);

  /*!
   * @brief Attempts to retrieve the textual content associated with an entity.
   *
   * Extracts the main identifier if available; otherwise, if the entity is a link node,
   * returns the link content.
   *
   * @param entityAddr sc-address of the entity.
   * @return Optional containing the extracted text if available; std::nullopt otherwise.
   */
  std::optional<std::string> SearchEntityText(ScAddr const & entityAddr);

  std::optional<std::string> SearchEntityAbbreviation(ScAddr const & entityAddr);

protected:
  utils::ScLogger m_logger;  ///< Internal logger instance for diagnostics.
};
