// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

/**
 * \file
 * Common exception classes
 */

#ifndef EDSAPI_ERRORS_H
#define EDSAPI_ERRORS_H

#include <stdexcept>
#include <string>

namespace eds
{

/**
 * Base exception class
 *
 * All EDS API exceptions derive from this class.
 */
class Error : public std::runtime_error
{
public:
  /// \private
  Error(const std::string& errorMessage);
  virtual ~Error() throw();
};


/**
 * Backend not found exception class
 *
 * Exceptions of this type are thrown when EDS API frontend cannot
 * load an appropriate backend dynamic library.
 */
class BackendNotFoundError : public Error
{
public:
  /// \private
  BackendNotFoundError(const std::string& backendName,
                       const std::string& backendType,
                       const std::string& backendVersion,
                       const std::string& errorMessage);
  virtual ~BackendNotFoundError() throw();

  /// File name of backend library (e.g. \em "edsapi_live_9_1.dll")
  const char* backendName() const;
  /// Backend type (e.g. \em "live" or \em "arch")
  const char* backendType() const;
  /// Backend version (e.g. \em "9.1")
  const char* backendVersion() const;
  /// %Error message returned from operating system
  const char* errorMessage() const;

private:
  const std::string _backendName;
  const std::string _backendType;
  const std::string _backendVersion;
  const std::string _errorMessage;
};


/**
 * Unsupported function exception class
 *
 * Exceptions of this type are thrown when currently loaded backend
 * does not support the method that was called.
 */
class UnsupportedFunctionError : public Error
{
public:
  /// \private
  UnsupportedFunctionError(const std::string& functionName,
                           const std::string& exportName,
                           const std::string& backendType,
                           const std::string& backendVersion);
  virtual ~UnsupportedFunctionError() throw();

  /// Name of unsupported function that was called
  const char* functionName() const;
  /// Name of backend's symbol (export) that corresponds
  /// to the unsupported function
  const char* exportName() const;
  /// Backend type (e.g. \em "live" or \em "arch")
  const char* backendType() const;
  /// Backend version (e.g. \em "9.1")
  const char* backendVersion() const;

private:
  const std::string _functionName;
  const std::string _exportName;
  const std::string _backendType;
  const std::string _backendVersion;
};


/**
 * Uninitialized client exception class
 *
 * Exceptions of this type are thrown when a method is called
 * on an uninitialized client.
 *
 * This typically happens as a result of trying to use a client
 * after LiveClient::shut() or ArchClient::shut() has been called.
 */
class UninitializedClientError : public Error
{
public:
  /// \private
  UninitializedClientError();
  virtual ~UninitializedClientError() throw();
};

}

#endif
