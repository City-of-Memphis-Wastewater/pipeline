// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

/*
 * file:	archeds.cpp
 * project:	ESSII
 * module:	API
 */

#include "archeds.h"
#include "../../utilseds2/deveds_texts.h"

#if !defined(WIN32) && !defined(_WIN32)
#include <dlfcn.h>
#endif

EDSFunction::EDSFunction(ArchEDSLib * _lib, const char * name)
{
  lib = _lib;
  func = lib->getFunction(name);
}

EDSFunction::~EDSFunction()
{
  if(lib)
    lib->destroyFunction(func);
}

void EDSFunction::pushPointParam(unsigned long sid,
                                 unsigned char bits,
                                 ArchEDSShadeMode options)
{
  if(lib)
    lib->pushPointParam(func,sid,bits,options);
}

void EDSFunction::pushTimestampParam(long ts)
{
  if(lib)
    lib->pushTimestampParam(func,ts);
}

void EDSFunction::pushValueParam(double v)
{
  if(lib)
    lib->pushValueParam(func,v);
}

void EDSFunction::clearParams()
{
  if(lib)
    lib->clearParams(func);
}


std::string ArchEDS::lib_search_path;

void ArchEDS::setLibrarySearchPath(const char *searchPath)
{
  lib_search_path = searchPath;
}

ArchEDS::ArchEDS()
{
  GetArchEDSLib func;

  std::string lib_path = lib_search_path;

#if defined(WIN32) || defined(_WIN32)
  if (lib_path != "")
    lib_path += "\\";
  lib_path += "archeds2.dll";
  lib_handle = LoadLibraryExA(lib_path.c_str(), NULL,
    LOAD_WITH_ALTERED_SEARCH_PATH);
#else
  if (lib_path != "")
    lib_path += "/";
  lib_path += "libarcheds2.so";
  lib_handle = dlopen(lib_path.c_str(), RTLD_NOW);
#endif
  if (!lib_handle)
    {
      // retry without search path
#if defined(WIN32) || defined(_WIN32)
      lib_handle = LoadLibraryExA("archeds2.dll", NULL,
        LOAD_WITH_ALTERED_SEARCH_PATH);
#else
      lib_handle = dlopen("libarcheds2.so", RTLD_NOW);
#endif
      if (!lib_handle)
        {
          fprintf( stderr,LD_LIBRARY_PATH_TEXT_LOG );
          lib = 0;
          conn = 0;
          return;
        }
    }
#if defined(WIN32) || defined(_WIN32)
  func = (GetArchEDSLib)GetProcAddress((struct HINSTANCE__ *)lib_handle, "getArchEDSLib");
#else
  func = (GetArchEDSLib)dlsym( lib_handle, "getArchEDSLib");
#endif

  if(!func)
    {
#if defined(WIN32) || defined(_WIN32)
      FreeLibrary((struct HINSTANCE__ *)lib_handle);
#else
      dlclose(lib_handle);
#endif
      lib = 0;
      conn = 0;
      lib_handle = 0;
      return;
    }

  lib = func(ARCH_EDS_LIB_VERSION);
  if(!lib) {
    conn = 0;
    return;
  }
  conn = lib->newConnection();
}

ArchEDS::~ArchEDS()
{
  if(conn)
    {
      lib->destroyConnection(conn);
      conn=0;
    }

  if(lib_handle)
    {
#if defined(WIN32) || defined(_WIN32)
      FreeLibrary((struct HINSTANCE__ *)lib_handle);
#else
      dlclose(lib_handle);
#endif
    }
}

int ArchEDS::init(const char * lhost, int lport,
                  const char * rhost, int rport,
                  int lport_range, int max_packet)
{
  if(!lib)
    return ARCH_EDS_LIB_ERR;
  return lib->init(conn,lhost,lport,
                   rhost,rport,lport_range,max_packet);
}

void ArchEDS::shut()
{
  if(lib)
    lib->shut(conn);
}

void ArchEDS::setupLogger(const char * str)
{
  if(lib)
    lib->setupLogger(str);
}

EDSFunction_ptr  ArchEDS::getFunction(const char * name)
{
  return EDSFunction_ptr(new EDSFunction(lib,name));
}

int ArchEDS::addQuery(EDSFunction_ptr& function)
{
  if(!lib)
    return ARCH_EDS_LIB_ERR;
  return lib->addQuery(conn, function->getDefinition());
}

int ArchEDS::getResponse(int id, double* value, char* qual)
{
  if(!lib)
    return ARCH_EDS_LIB_ERR;
  return lib->getResponse(conn, id, value, qual);
}

void ArchEDS::clear()
{
  if(lib)
    lib->clearAll(conn);
}

int ArchEDS::executeQueries()
{
  if(lib)
    return lib->executeQueries(conn);
  return ARCH_EDS_LIB_ERR;
}

int ArchEDS::executeQuery(EDSFunction_ptr& function, double* value, char* qual)
{
  if(!lib)
    return ARCH_EDS_LIB_ERR;
  return lib->executeQuery(conn,function->getDefinition(), value, qual);
}

int ArchEDS::addTabTrend(EDSTabTrend_ptr& trend,
                         ArchEDSShadeMode shade_mode)
{
  if(!lib)
    return ARCH_EDS_LIB_ERR;

  return(lib->addTabTrend(conn,trend->getDefinition(),shade_mode));
}

int ArchEDS::executeTabTrends(long ref_time, long range, long step, bool useDST)
{
  if(lib)
    return lib->executeTabTrends(conn, ref_time, range, step, useDST);
  return ARCH_EDS_LIB_ERR;
}

ArchEDSTrendRow * ArchEDS::fetchTabTrendRow()
{
  if(!lib)
    return 0;
  return lib->fetchTabTrendRow(conn);
}

void ArchEDS::destroyTrendRow(ArchEDSTrendRow * row)
{
  if(lib)
    lib->destroyTrendRow(row);
}

int ArchEDS::writeShades()
{
  if(!lib)
    return ARCH_EDS_LIB_ERR;
  return lib->writeShades(conn);
}

int ArchEDS::addShadeValue(long sid,
                           long start_ts,
                           long end_ts,
                           float val,
                           char qual)
{
  if(!lib)
    return ARCH_EDS_LIB_ERR;
  return lib->addShadeValue(conn,sid,start_ts,end_ts,val,qual);
}

EDSTabTrend::EDSTabTrend(ArchEDSLib * _lib, long sid, const char * func)
{
  lib = _lib;
  trend = lib->createTabTrend(sid,func);
}

EDSTabTrend::~EDSTabTrend()
{
  if(lib)
    lib->destroyTrend(trend);
}

void EDSTabTrend::clearParams()
{
  if(lib)
    lib->clearTrendParams(trend);
}

void EDSTabTrend::pushParam(double v)
{
  if(lib)
    lib->pushTrendParam(trend,v);
}

