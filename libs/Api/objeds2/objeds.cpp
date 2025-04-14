// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

/*
 * file:	objeds.cpp
 * project:	ESSII
 * module:	API
 */

#include "objeds.h"
#include "../utilseds2/deveds_texts.h"

#include <string.h>

#if !defined(WIN32) && !defined(_WIN32)
#include <dlfcn.h>
#endif


EDSGroups::EDSGroups()
{
  memset(groups, 0, OBJ_EDS_MAX_GROUPS / 8);
}

EDSGroups::EDSGroups(const ObjEDSGroups objEDSGroups)
{
  memcpy(groups, objEDSGroups, OBJ_EDS_MAX_GROUPS / 8);
}

bool EDSGroups::hasPermission(int index) const
{
  if (index >= OBJ_EDS_MAX_GROUPS || index < 0)
    return false;
  if (groups[index / 8] & (0x01 << (index % 8)))
    return true;
  return false;
}

void EDSGroups::setPermission(int index, bool granted)
{
  if (index >= OBJ_EDS_MAX_GROUPS || index < 0)
    return;
  unsigned char b = groups[index / 8];
  unsigned char mask = ~(0x01 << (index % 8));
  unsigned char flag = (granted ? 0x01 : 0x00) << (index % 8);
  groups[index / 8] = (b & mask) | flag;
}

EDSMd5::EDSMd5()
{
  memset(md5, 0, 16);
}

EDSMd5::EDSMd5(const ObjEDSMd5 objEDSMd5)
{
  memcpy(md5, objEDSMd5, 16);
}

EDSGroupObject::EDSGroupObject(ObjEDSLib * _lib, p_ObjEDSGroupObject _group)
  : lib(_lib), group(_group)
{ }

EDSGroupObject::~EDSGroupObject()
{
  lib->destroyGroupObject(group);
}

EDSGlobalSource::EDSGlobalSource(ObjEDSLib * _lib,
                                 p_ObjEDSGlobalSource _globalSource)
  : lib(_lib), globalSource(_globalSource)
{ }

EDSGlobalSource::~EDSGlobalSource()
{
  lib->destroySource(globalSource);
}

EDSGlobalObject::EDSGlobalObject(ObjEDSLib * _lib,
                                 p_ObjEDSGlobalObject _globalObject)
  : lib(_lib), globalObject(_globalObject)
{ }

EDSGlobalObject::~EDSGlobalObject()
{
  lib->destroyGlobalObject(globalObject);
}

EDSUser::EDSUser(ObjEDSLib * _lib, p_ObjEDSUser _user)
  : lib(_lib), user(_user)
{ }

EDSUser::~EDSUser()
{
  lib->destroyUser(user);
}

EDSTask::EDSTask(ObjEDSLib * _lib, p_ObjEDSTask _task)
  : lib(_lib), task(_task)
{ }

EDSTask::~EDSTask()
{
  lib->destroyTask(task);
}

ObjEDS::ObjEDS()
{
  GetObjEDSLib func;
#if defined(WIN32) || defined(_WIN32)
  lib_handle = LoadLibraryA("objeds2.dll");
#else
  lib_handle = dlopen( "libobjeds2.so", RTLD_NOW );
#endif
  if (!lib_handle)
    {
      fprintf( stderr,LD_LIBRARY_PATH_TEXT_LOG );
      lib = 0;
      conn = 0;
      return;
    }
#if defined(WIN32) || defined(_WIN32)
  func = (GetObjEDSLib)GetProcAddress((struct HINSTANCE__ *)lib_handle, "getObjEDSLib");
#else
  func = (GetObjEDSLib)dlsym( lib_handle, "getObjEDSLib");
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

  lib = func(OBJ_EDS_LIB_VERSION);
  if(!lib) {
    conn = 0;
    return;
  }
  conn = lib->newConnection();
}

ObjEDS::~ObjEDS()
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

int ObjEDS::init(const char * lhost, int lport,
                 const char * rhost, int rport,
                 const char * user, const char * password,
                 int lport_range, int max_packet)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->init(conn, lhost, lport, rhost, rport,
    user, password, lport_range, max_packet);
}

void ObjEDS::shut()
{
  if (lib)
    lib->shut(conn);
}

void ObjEDS::setupLogger(const char * str)
{
  if (lib)
    lib->setupLogger(str);
}

int ObjEDS::synchronize()
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->synchronize(conn);
}

int ObjEDS::flushGlobalCacheFile()
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->flushGlobalCacheFile(conn);
}

int ObjEDS::groupsChanged()
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->groupsChanged(conn);
}

int ObjEDS::getSecurityGroup(unsigned int group_index,
                             EDSGroupObject_ptr & out_group)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  p_ObjEDSGroupObject objEDSGroup;
  int result = lib->getSecurityGroup(conn, group_index, &objEDSGroup);
  if (result < 0)
    return result;
  out_group = EDSGroupObject_ptr(new EDSGroupObject(lib, objEDSGroup));
  return 0;
}

int ObjEDS::getTechGroup(unsigned int group_index,
                         EDSGroupObject_ptr & out_group)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  p_ObjEDSGroupObject objEDSGroup;
  int result = lib->getTechGroup(conn, group_index, &objEDSGroup);
  if (result < 0)
    return result;
  out_group = EDSGroupObject_ptr(new EDSGroupObject(lib, objEDSGroup));
  return 0;
}

int ObjEDS::alterSecurityGroup(unsigned int group_index, const char * name,
                               const char * desc)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->alterSecurityGroup(conn, group_index, name, desc);
}

int ObjEDS::alterTechGroup(unsigned int group_index, const char * name,
                           const char * desc)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->alterTechGroup(conn, group_index, name, desc);
}

EDSGlobalSource_ptr ObjEDS::newSource(unsigned int id, const char * name,
                                      const char * desc, const char * host,
                                      const char * p_pref, const char * p_post,
                                      const EDSGroups & sg, const EDSGroups & tg,
                                      ObjEDSSourceKind kind, unsigned int options)
{
  if (!lib)
    return EDSGlobalSource_ptr();
  return EDSGlobalSource_ptr(new EDSGlobalSource(lib,
    lib->newSource(id, name,desc, host, p_pref, p_post, sg.groups, tg.groups,
      kind, options)));
}

int ObjEDS::sourcesChanged()
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->sourcesChanged(conn);
}

int ObjEDS::getSourceCount()
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->getSourceCount(conn);
}

int ObjEDS::getSourceByIndex(unsigned int source_index,
                             EDSGlobalSource_ptr & out_source)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  p_ObjEDSGlobalSource objEDSSrc;
  int result = lib->getSourceByIndex(conn, source_index, &objEDSSrc);
  if (result < 0)
    return result;
  out_source = EDSGlobalSource_ptr(new EDSGlobalSource(lib, objEDSSrc));
  return 0;
}

int ObjEDS::getSourceById(unsigned int source_id,
                          EDSGlobalSource_ptr & out_source)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  p_ObjEDSGlobalSource objEDSSrc;
  int result = lib->getSourceById(conn, source_id, &objEDSSrc);
  if (result < 0)
    return result;
  out_source = EDSGlobalSource_ptr(new EDSGlobalSource(lib, objEDSSrc));
  return 0;
}

int ObjEDS::createSource(const EDSGlobalSource & source)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->createSource(conn, source.globalSource);
}

int ObjEDS::alterSource(unsigned int source_index,
                        const EDSGlobalSource & source)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->alterSource(conn, source_index, source.globalSource);
}

int ObjEDS::removeSource(unsigned int source_index)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->removeSource(conn, source_index);
}

EDSGlobalObject_ptr ObjEDS::newGlobalObject(unsigned int source_id,
                                            const char * file,
                                            const char * name,
                                            unsigned long data_ts,
                                            const EDSGroups & sg,
                                            const EDSGroups & tg,
                                            const EDSMd5 & md5)
{
  if (!lib)
    return EDSGlobalObject_ptr();
  return EDSGlobalObject_ptr(new EDSGlobalObject(lib,
    lib->newGlobalObject(source_id, file, name, data_ts,
      sg.groups, tg.groups, md5.md5)));
}

int ObjEDS::globalObjectsChanged()
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->globalObjectsChanged(conn);
}

int ObjEDS::getGlobalObjectCount()
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->getGlobalObjectCount(conn);
}

int ObjEDS::getGlobalObjectByIndex(unsigned int global_obj_index,
                                   EDSGlobalObject_ptr & out_global_obj)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  p_ObjEDSGlobalObject objEDSObj;
  int result = lib->getGlobalObjectByIndex(conn, global_obj_index, &objEDSObj);
  if (result < 0)
    return result;
  out_global_obj = EDSGlobalObject_ptr(new EDSGlobalObject(lib, objEDSObj));
  return 0;
}

int ObjEDS::getGlobalObjectByFileName(unsigned int source_id,
                                      const char * file_name,
                                      EDSGlobalObject_ptr & out_global_obj)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  p_ObjEDSGlobalObject objEDSObj;
  int result = lib->getGlobalObjectByFileName(conn, source_id,
    file_name, &objEDSObj);
  if (result < 0)
    return result;
  out_global_obj = EDSGlobalObject_ptr(new EDSGlobalObject(lib, objEDSObj));
  return 0;
}

int ObjEDS::createGlobalObject(const EDSGlobalObject & global_obj)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->createGlobalObject(conn, global_obj.globalObject);
}

int ObjEDS::alterGlobalObject(unsigned int global_obj_index,
                              const EDSGlobalObject & global_obj)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->alterGlobalObject(conn, global_obj_index,
    global_obj.globalObject);
}

int ObjEDS::removeGlobalObject(unsigned int global_obj_index)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->removeGlobalObject(conn, global_obj_index);
}

int ObjEDS::uploadGlobalObject(unsigned int global_obj_index,
                               const char * source_file)
{
  if (!lib)
      return OBJ_EDS_LIB_ERR;
  return lib->uploadGlobalObject(conn, global_obj_index, source_file);
}

int ObjEDS::downloadGlobalObject(unsigned int global_obj_index,
                                 const char * destination_file)
{
  if (!lib)
      return OBJ_EDS_LIB_ERR;
  return lib->downloadGlobalObject(conn, global_obj_index, destination_file);
}

int ObjEDS::userName(std::string & userName)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  char tmpStr[128];
  int length = lib->userName(conn, tmpStr, sizeof(tmpStr));
  if (length < 0)
    return length;

  if (static_cast<unsigned>(length) < sizeof(tmpStr))
  {
    // fetched correctly
    userName = tmpStr;
  }
  else
  {
    // couldn't fetch full name, use dynamic array now
    auto tmpDynStr = std::unique_ptr<char[]>(new char[length + 1]);
    length = lib->userName(conn, tmpDynStr.get(), length + 1);
    if (length >= 0)
      userName = tmpDynStr.get();
  }

  return length;
}

int ObjEDS::getCurrentUserSG(EDSGroups & sg)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  ObjEDSGroups tmpSg;
  int result = lib->getCurrentUserSG(conn, tmpSg);
  if (result < 0)
    return result;
  sg = EDSGroups(tmpSg);
  return 0;
}

int ObjEDS::isCurrentUserAdmin()
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->isCurrentUserAdmin(conn);
}

EDSUser_ptr ObjEDS::newUser(const char * name, const char * desc,
                            const EDSGroups & sg, const char * auth_info,
                            bool locked)
{
  if (!lib)
    return EDSUser_ptr();
  return EDSUser_ptr(new EDSUser(lib,
    lib->newUser(name, desc, sg.groups, auth_info, locked)));
}

int ObjEDS::usersChanged()
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->usersChanged(conn);
}

int ObjEDS::getUserCount()
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->getUserCount(conn);
}

int ObjEDS::getUserByIndex(unsigned int user_index, EDSUser_ptr & out_user)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  p_ObjEDSUser objEDSUser;
  int result = lib->getUserByIndex(conn, user_index, &objEDSUser);
  if (result < 0)
    return result;
  out_user = EDSUser_ptr(new EDSUser(lib, objEDSUser));
  return 0;
}

int ObjEDS::getUserByName(const char * name, EDSUser_ptr & out_user)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  p_ObjEDSUser objEDSUser;
  int result = lib->getUserByName(conn, name, &objEDSUser);
  if (result < 0)
    return result;
  out_user = EDSUser_ptr(new EDSUser(lib, objEDSUser));
  return 0;
}

int ObjEDS::createUser(const EDSUser & user)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->createUser(conn, user.user);
}

int ObjEDS::importUser(const EDSUser & user)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->importUser(conn, user.user);
}

int ObjEDS::alterUser(const EDSUser & user)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->alterUser(conn, user.user);
}

int ObjEDS::removeUser(const char * user_name)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->removeUser(conn, user_name);
}

int ObjEDS::mayCurrentUserAccessObject(const char * source_name,
                                       const char * object_name)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->mayCurrentUserAccessObject(conn, source_name, object_name);
}

int ObjEDS::getUserSG(const char * user_name, EDSGroups & sg)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  ObjEDSGroups tmpSg;
  int result = lib->getUserSG(conn, user_name, tmpSg);
  if (result < 0)
    return result;
  sg = EDSGroups(tmpSg);
  return 0;
}

int ObjEDS::userBelongsToSGByName(const char * user_name,
                                  const char * group_name)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->userBelongsToSGByName(conn, user_name, group_name);
}

int ObjEDS::userBelongsToSGByIndex(const char * user_name,
                                   unsigned int group_index)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->userBelongsToSGByIndex(conn, user_name, group_index);
}

int ObjEDS::isUserAdmin(const char * user_name)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->isUserAdmin(conn, user_name);
}

EDSTask_ptr ObjEDS::newTask(unsigned int ref_task_idx,
                      unsigned int ref_ts,
                      unsigned int run_ts,
                      int run_delay,
                      const char * type,
                      ObjEDSTaskPriority priority,
                      const char * params,
                      ObjEDSTaskStatus status,
                      unsigned int task_ts,
                      unsigned int task_usec,
                      unsigned int finished,
                      unsigned int retries)
{
  if (!lib)
    return EDSTask_ptr();
  return EDSTask_ptr(new EDSTask(lib,
    lib->newTask(ref_task_idx, ref_ts, run_ts, run_delay, type, priority,
      params, status, task_ts, task_usec, finished, retries)));
}

int ObjEDS::tasksChanged()
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->tasksChanged(conn);
}

int ObjEDS::createTask(const EDSTask & task)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->createTask(conn, task.task);
}

int ObjEDS::alterTask(unsigned int task_index, const EDSTask & task)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->alterTask(conn, task_index, task.task);
}

int ObjEDS::removeTask(unsigned int task_index)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->removeTask(conn, task_index);
}

int ObjEDS::getTaskByIndex(unsigned int task_index,
                           EDSTask_ptr & out_task)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  p_ObjEDSTask objEDSTask;
  int result = lib->getTaskByIndex(conn, task_index, &objEDSTask);
  if (result < 0)
    return result;
  out_task = EDSTask_ptr(new EDSTask(lib, objEDSTask));
  return 0;
}

int ObjEDS::getTaskById(unsigned int task_id,
                        EDSTask_ptr & out_task)
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  p_ObjEDSTask objEDSTask;
  int result = lib->getTaskById(conn, task_id, &objEDSTask);
  if (result < 0)
    return result;
  out_task = EDSTask_ptr(new EDSTask(lib, objEDSTask));
  return 0;
}

int ObjEDS::getTaskCount()
{
  if (!lib)
    return OBJ_EDS_LIB_ERR;
  return lib->getTaskCount(conn);
}
