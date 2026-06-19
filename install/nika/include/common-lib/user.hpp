#pragma once

#include <sc-memory/sc_addr.hpp>

class AdvancedAgentContext;

/*!
 * @class User
 * @brief Represents a user in the knowledge base, providing methods to manage user identifiers.
 *
 * The User class encapsulates a user node in sc-memory, offering methods to set, retrieve, and manage
 * user identifiers. It integrates with AdvancedAgentContext for context-aware operations and supports
 * both sc-address and string-based identifier management.
 *
 * Features:
 * - Constructs from an AdvancedAgentContext and user sc-address.
 * - Retrieves the sc-address of the user's identifier link.
 * - Sets the user's identifier using a string value.
 * - Retrieves the user's identifier as a string value.
 *
 * This class is typically used in dialogue and authentication subsystems to manage and query user identities.
 *
 * @note This class is intended for internal use within user management and dialogue subsystems.
 *
 * @see AdvancedAgentContext
 * @see ScAddr
 */
class User : public ScAddr
{
  friend class AdvancedAgentContext;

public:
  /*!
   * @brief Retrieves the sc-address of the user's identifier link.
   * @return sc-address of the identifier link.
   * @throws utils::ExceptionInvalidState if no identifier is found or if multiple identifiers exist.
   */
  ScAddr GetID() const;

  /*!
   * @brief Sets the user's identifier using a string value.
   * @param ID The new identifier string.
   */
  void SetID(std::string const & ID);

  /*!
   * @brief Retrieves the user's identifier as a string value.
   * @return The identifier string (without any prefix).
   */
  std::string GetIDValue() const;

protected:
  AdvancedAgentContext & m_context;  ///< Reference to the advanced agent context.

  /*!
   * @brief Constructs a User instance.
   * @param context Reference to the AdvancedAgentContext.
   * @param userAddr sc-address of the user node.
   */
  User(AdvancedAgentContext & context, ScAddr const & userAddr);
};
