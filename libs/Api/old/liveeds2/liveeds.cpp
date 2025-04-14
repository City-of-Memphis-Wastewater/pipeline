// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

#include "liveeds.h"
#include "../../utilseds2/deveds_texts.h"

#include <stdio.h>

#ifndef WIN32
#include <dlfcn.h>
#endif

std::string LiveEDS::lib_path;

const char* LiveEDS::libraryPath()
{
  return lib_path.c_str();
}

void LiveEDS::setLibraryPath(const char* path)
{
  lib_path = (path != 0) ? path : "";
}


LiveEDS::LiveEDS()
{
  GetLiveEDSLib func = 0;

  std::string path;
#if defined WIN32
  if (lib_path != "")
    path = lib_path + "\\liveeds2.dll";
  else
    path = "liveeds2.dll";
#else
  if (lib_path != "")
    path = lib_path + "/libliveeds2.so";
  else
    path = "libliveeds2.so";
#endif

#if defined WIN32
  lib_handle = LoadLibraryA(path.c_str());
#else
  lib_handle = dlopen(path.c_str(), RTLD_NOW);
#endif
  if (!lib_handle)
    {
#if defined WIN32
      LPVOID errorMessage;

      if (FormatMessage(
          FORMAT_MESSAGE_ALLOCATE_BUFFER |
          FORMAT_MESSAGE_FROM_SYSTEM |
          FORMAT_MESSAGE_IGNORE_INSERTS,
          NULL,
          GetLastError(),
          MAKELANGID(LANG_NEUTRAL, SUBLANG_DEFAULT), // Default language
          (LPTSTR)&errorMessage,
          0,
          NULL) == 0)
        errorMessage = 0;

      std::string errorMessageStr = "Unknown error";
      if (errorMessage != 0)
      {
        errorMessageStr = static_cast<char*>(errorMessage);
        LocalFree(errorMessage);
      }

      fprintf( stderr, "%s:%d - LoadLibraryA(\"%s\") failed, %u - %s\n",
        __FILE__, __LINE__, path.c_str(), GetLastError(), errorMessageStr.c_str() );
#else
      fprintf( stderr, "%s:%d - dlopen(\"%s\", RTLD_NOW ) failed, %s\n",
        __FILE__, __LINE__, path.c_str(), dlerror() );
      fprintf( stderr,LD_LIBRARY_PATH_TEXT_LOG );
#endif
      lib = 0;
      conn = 0;
      return;
    }
#if defined WIN32
  func = (GetLiveEDSLib)GetProcAddress ((HMODULE)lib_handle, "getLiveEDSLib");
#else
  func = (GetLiveEDSLib)dlsym( lib_handle, "getLiveEDSLib");
#endif
  if(!func)
    {
#ifdef WIN32
      FreeLibrary((HMODULE)lib_handle);
#else
      dlclose(lib_handle);
#endif
      conn=0;
      lib_handle = 0;
      lib = 0;
      return;
    }

  lib = func(LIVE_EDS_LIB_VERSION);
  if(!lib) {
    conn = 0;
    return;
  }
  conn = lib->newConnection();
}//LiveEDS

LiveEDS::~LiveEDS()
{
  if(conn)
    {
      lib->destroyConnection(conn);
      conn=0;
    }

  if(lib_handle)
    {
#ifdef WIN32
      FreeLibrary((HMODULE)lib_handle);
#else
      dlclose(lib_handle);
#endif
    }
}

void LiveEDS::setupLogger(const char * str)
{
  if(!lib)
    return;
  lib->setupLogger(str);
}

int LiveEDS::init(LiveEDSMode mode, const char * lhost, int lport,
                  const char * rhost, int rport,
                  int lport_range,
                  int max_packet)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->init(conn,mode,lhost, lport, rhost,
                   rport, lport_range, max_packet);
}

int LiveEDS::authInit(const char * user, const char * password,
                      const char * lhost, int lport,
                      const char * rhost, int rport,
                      int lport_range,
                      int max_packet)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->authInit(conn, user, password, lhost, lport, rhost,
                       rport, lport_range, max_packet);
}

int LiveEDS::shut()
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  lib->destroyConnection(conn);
  conn = lib->newConnection();
  return conn==0;
}

long LiveEDS::findByIESS(const char * iess)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->findByIESS(conn, iess);
}

long LiveEDS::findByIESS_NoCase(const char * iess)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->findByIESS_NoCase(conn, iess);
}

long LiveEDS::findByIDCS(const char * idcs,const char * zd)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->findByIDCS(conn,idcs,zd);
}

long LiveEDS::findByIDCS_NoCase(const char * idcs,const char * zd)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->findByIDCS_NoCase(conn,idcs,zd);
}

long LiveEDS::getSID(long lid)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->getSID(conn,lid);
}

int LiveEDS::setInput(long lid)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->setInput(conn,lid);
}

int LiveEDS::setOutput(long lid)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->setOutput(conn,lid);
}

int LiveEDS::unsetInput(long lid)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->unsetInput(conn,lid);
}

int LiveEDS::unsetOutput(long lid)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->unsetOutput(conn,lid);
}

int LiveEDS::synchronizeInput()
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->synchronizeInput(conn);
}

int LiveEDS::synchronizeOutput()
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->synchronizeOutput(conn);
}

int LiveEDS::read(long lid, float * val, char * qual)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->readValue(conn,lid,val,qual);
}

int LiveEDS::read(long lid, double * val, char * qual)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->readDouble(conn,lid,val,qual);
}

int LiveEDS::read(long lid, unsigned long * val, char * qual)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->readPacked(conn,lid,val,qual);
}

int LiveEDS::read(long lid, int64_t * val, char * qual)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->readInt64(conn,lid,val,qual);
}

int LiveEDS::read(long lid, unsigned char * val, char * qual)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->readBinary(conn,lid,val,qual);
}

int LiveEDS::write(long lid, float * val, char * qual)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->writeValue(conn,lid,val,qual);
}

int LiveEDS::write(long lid, double * val, char * qual)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->writeDouble(conn,lid,val,qual);
}

int LiveEDS::write(long lid, unsigned long * val, char * qual)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->writePacked(conn,lid,val,qual);
}

int LiveEDS::write(long lid, int64_t * val, char * qual)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->writeInt64(conn,lid,val,qual);
}

int LiveEDS::write(long lid, unsigned char * val, char * qual)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->writeBinary(conn,lid,val,qual);
}

int LiveEDS::fieldIdFromName(const char* name)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->fieldIdFromName(name);
}

int LiveEDS::fieldIdFromWDPFName(const char* name)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->fieldIdFromWDPFName(name);
}

int LiveEDS::readField(long lid, int field_id, int * val)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->readFieldInt(conn, lid, field_id, val);
}

int LiveEDS::readField(long lid, int field_id, float * val)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->readFieldValue(conn, lid, field_id, val);
}

int LiveEDS::readField(long lid, int field_id, double * val)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->readFieldDouble(conn, lid, field_id, val);
}

int LiveEDS::readField(long lid, int field_id, char * buffer, int buffer_size)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->readFieldString(conn, lid, field_id, buffer, buffer_size);
}

int LiveEDS::readField(long lid, const char * field_name, int * val)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->readFieldIntByName(conn, lid, field_name, val);
}

int LiveEDS::readWDPFField(long lid, const char * field_name, int * val)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->readFieldIntByWDPFName(conn, lid, field_name, val);
}

int LiveEDS::readField(long lid, const char * field_name, float * val)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->readFieldValueByName(conn, lid, field_name, val);
}

int LiveEDS::readWDPFField(long lid, const char * field_name, float * val)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->readFieldValueByWDPFName(conn, lid, field_name, val);
}

int LiveEDS::readField(long lid, const char * field_name, double * val)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->readFieldDoubleByName(conn, lid, field_name, val);
}

int LiveEDS::readWDPFField(long lid, const char * field_name, double * val)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->readFieldDoubleByWDPFName(conn, lid, field_name, val);
}

int LiveEDS::readField(long lid, const char * field_name,
                       char * buffer,
                       int buffer_size)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->readFieldStringByName(conn, lid, field_name,
                                    buffer, buffer_size);
}

int LiveEDS::readWDPFField(long lid, const char * field_name,
                       char * buffer,
                       int buffer_size)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->readFieldStringByWDPFName(conn, lid, field_name,
                                    buffer, buffer_size);
}

int LiveEDS::writeStatus(long lid, unsigned int value, unsigned int mask)
{
  if (!lib)
    return LIVE_EDS_LIB_ERR;

  return lib->writeStatus(conn, lid, value, mask);
}

int LiveEDS::writeXSTn(long lid, int n, int value, int mask)
{
  if(!lib)
    return LIVE_EDS_LIB_ERR;
  return lib->writeXSTn(conn,lid,n,value,mask);
}
