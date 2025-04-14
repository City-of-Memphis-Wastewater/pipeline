// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

#ifndef EDSAPI_BACKEND_H
#define EDSAPI_BACKEND_H

#include <string>

#if defined(_WIN32) || defined(__WIN32__)
#include <windows.h>
#else
#include <dlfcn.h>
#endif


namespace eds
{

namespace detail
{

class Backend
{
public:
  Backend(const char* type, const char* version);
  ~Backend();

  void* resolveExport(const char* exportName) const;

  const char* type() const;
  const char* version() const;

private:
  std::string fileName() const;
  void load();

#if defined(_WIN32) || defined(__WIN32__)
  HMODULE _handle;
#else
  void* _handle;
#endif

  const std::string _type;
  const std::string _version;
};

}

}

#endif
