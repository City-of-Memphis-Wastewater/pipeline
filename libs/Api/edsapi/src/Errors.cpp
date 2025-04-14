// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

#include "../include/Errors.h"

namespace eds
{

/** Error **/

Error::Error(const std::string& errorMessage)
  : std::runtime_error(errorMessage)
{
}

Error::~Error() throw()
{
}


/** BackendNotFoundError **/

BackendNotFoundError::BackendNotFoundError(
    const std::string& backendName, const std::string& backendType,
    const std::string& backendVersion, const std::string& errorMessage)
  : Error(
      std::string("Backend ") + backendName + " (type '" +
        backendType + "', version " + backendVersion + ") not found " +
        "(" + errorMessage + ")"),
    _backendName(backendName),
    _backendType(backendType),
    _backendVersion(backendVersion),
    _errorMessage(errorMessage)
{
}

BackendNotFoundError::~BackendNotFoundError() throw()
{
}

const char* BackendNotFoundError::backendName() const
{
  return _backendName.c_str();
}

const char* BackendNotFoundError::backendType() const
{
  return _backendType.c_str();
}

const char* BackendNotFoundError::backendVersion() const
{
  return _backendVersion.c_str();
}

const char* BackendNotFoundError::errorMessage() const
{
  return _errorMessage.c_str();
}


/** UnsupportedFunctionError **/

UnsupportedFunctionError::UnsupportedFunctionError(
    const std::string& functionName, const std::string& exportName,
    const std::string& backendType, const std::string& backendVersion)
  : Error(
      std::string("Unsupported function ") + functionName +
      " (export " + exportName + ") called from " + backendType +
      " backend version " + backendVersion),
    _functionName(functionName),
    _exportName(exportName),
    _backendType(backendType),
    _backendVersion(backendVersion)
{
}

UnsupportedFunctionError::~UnsupportedFunctionError() throw()
{
}

const char* UnsupportedFunctionError::functionName() const
{
  return _functionName.c_str();
}

const char* UnsupportedFunctionError::exportName() const
{
  return _exportName.c_str();
}

const char* UnsupportedFunctionError::backendType() const
{
  return _backendType.c_str();
}

const char* UnsupportedFunctionError::backendVersion() const
{
  return _backendType.c_str();
}


/** UninitializedClientError **/

UninitializedClientError::UninitializedClientError()
  : Error("Operation attempted on uninitialized client")
{
}

UninitializedClientError::~UninitializedClientError() throw()
{
}

}
