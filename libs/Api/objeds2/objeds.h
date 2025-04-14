// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

/*
 * file:	objeds.h
 * project:	ESSII
 * module:	API
 */

#ifndef _OBJEDS_H_
#define _OBJEDS_H_

#include "objeds_lib.h"

#if defined(_WIN32) || defined(__WIN32__)
# if !defined(WIN32)
#  define WIN32
# endif
# include <windows.h>
#endif

#include <memory>
#include <string>

#define OBJ_EDS_LIB_ERR -1000

class EDSGroups
{
 public:
  EDSGroups();
  EDSGroups(const ObjEDSGroups objEDSGroups);

  bool hasPermission(int index) const;
  void setPermission(int index, bool granted);

 private:
  ObjEDSGroups groups;

  friend class ObjEDS;
};

class EDSMd5
{
 public:
   EDSMd5();
   EDSMd5(const ObjEDSMd5 objEDSMd5);

   const char *rawDigest() const
   { return (const char *)md5; }
   unsigned int size() const
   { return 16; }

 private:
  ObjEDSMd5 md5;

  friend class ObjEDS;
};

class EDSGroupObject
{
 public:
  ~EDSGroupObject();

  int index() const
  { return group->index; }
  const char * name() const
  { return group->name; }
  const char * desc() const
  { return group->desc; }

 private:
   EDSGroupObject(ObjEDSLib * lib, p_ObjEDSGroupObject group);

   EDSGroupObject(const EDSGroupObject &);
   EDSGroupObject & operator =(const EDSGroupObject &);

   ObjEDSLib * lib;
   p_ObjEDSGroupObject group;

   friend class ObjEDS;
};
typedef std::unique_ptr<EDSGroupObject> EDSGroupObject_ptr;

class EDSGlobalSource
{
 public:
  ~EDSGlobalSource();

  unsigned int id() const
  { return globalSource->id; }
  const char * name() const
  { return globalSource->name; }
  const char * desc() const
  { return globalSource->desc; }
  const char * host() const
  { return globalSource->host; }
  const char * pPref() const
  { return globalSource->p_pref; }
  const char * pPost() const
  { return globalSource->p_post; }
  const EDSGroups sg() const
  { return EDSGroups(globalSource->sg); }
  const EDSGroups tg() const
  { return EDSGroups(globalSource->tg); }
  ObjEDSSourceKind kind() const
  { return globalSource->kind; }
  unsigned int options() const
  { return globalSource->options; }

 private:
  EDSGlobalSource(ObjEDSLib * lib, p_ObjEDSGlobalSource globalSource);

  EDSGlobalSource(const EDSGlobalSource &);
  EDSGlobalSource & operator =(const EDSGlobalSource &);

  ObjEDSLib * lib;
  p_ObjEDSGlobalSource globalSource;

  friend class ObjEDS;
};
typedef std::unique_ptr<EDSGlobalSource> EDSGlobalSource_ptr;

class EDSGlobalObject
{
 public:
  ~EDSGlobalObject();

  unsigned int sourceId() const
  { return globalObject->source_id; }
  const char * file() const
  { return globalObject->file; }
  const char * name() const
  { return globalObject->name; }
  unsigned long dataTS() const
  { return globalObject->data_ts; }
  EDSGroups sg() const
  { return EDSGroups(globalObject->sg); }
  EDSGroups tg() const
  { return EDSGroups(globalObject->tg); }
  EDSMd5 md5() const
  { return EDSMd5(globalObject->md5); }

private:
  EDSGlobalObject(ObjEDSLib * lib, p_ObjEDSGlobalObject globalObject);

  EDSGlobalObject(const EDSGlobalObject &);
  EDSGlobalObject & operator =(const EDSGlobalObject &);

  ObjEDSLib * lib;
  p_ObjEDSGlobalObject globalObject;

  friend class ObjEDS;
};
typedef std::unique_ptr<EDSGlobalObject> EDSGlobalObject_ptr;

class EDSUser
{
 public:
  ~EDSUser();

  const char * name() const
  { return user->name; }
  const char * desc() const
  { return user->desc; }
  EDSGroups sg() const
  { return EDSGroups(user->sg); }
  const char * authInfo() const
  { return user->auth_info; }
  bool locked() const
  { return user->locked!=0; }

 private:
   EDSUser(ObjEDSLib * lib, p_ObjEDSUser user);

   EDSUser(const EDSUser &);
   EDSUser & operator =(const EDSUser &);

   ObjEDSLib * lib;
   p_ObjEDSUser user;

   friend class ObjEDS;
};
typedef std::unique_ptr<EDSUser> EDSUser_ptr;

class EDSTask
{
 public:
    ~EDSTask();

 unsigned int idx() const
 { return task->ref_task_idx; }
 unsigned int ref_ts() const
 { return task->ref_ts; }
 unsigned int run_ts() const
 { return task->run_ts; }
 int run_delay() const
 { return task->run_delay; }
 const char * type() const
 { return task->type; }
 ObjEDSTaskPriority priority() const
 { return task->priority; }
 const char * params() const
 { return task->params; }
 ObjEDSTaskStatus status() const
 { return task->status; }
 unsigned int task_ts() const
 { return task->task_ts; }
 unsigned int task_usec() const
 { return task->task_usec; }
 unsigned int finished() const
 { return task->finished; }
 int retries() const
 { return task->retries; }
 
 private:
  EDSTask(ObjEDSLib * lib, p_ObjEDSTask task);

  EDSTask(const EDSTask &);
  EDSTask & operator =(const EDSTask &);

  ObjEDSLib * lib;
  p_ObjEDSTask task;

  friend class ObjEDS;
};
typedef std::unique_ptr<EDSTask> EDSTask_ptr;

class ObjEDS
{
 public:
  /** Default wrapper constructor - creates wrapper and loads library */
  ObjEDS();
  /** Frees library */
  virtual ~ObjEDS();

  /** Initializes connection structure using parameters:
      local host, local port, remote host, remote port, max packet size.
      Mode describes what functions should be available. */
  int init(const char * lhost, int lport,
           const char * rhost, int rport,
           const char * user, const char * password,
           int lport_range, int max_packet);

  /** Shuts connection to EDS Archive Server */
  void shut();

  /** Setups logger using setup string.
      For example: str="debug=7 logger=console:7 subsystems=ALL"*/
  void setupLogger(const char * str);

  /** Synchronizes with ObjServer. This call also updates state flags.
      Returns <0 on error, 0 on success. */
  int synchronize();

  /** Flushes object cache. Returns 0 on success, <0 on error. */
  int flushGlobalCacheFile();

  /** Returns 1 if groups have changed since last synchronization,
      0 if not, <0 on error. */
  int groupsChanged();

  /** Returns (in out_group argument) security group identified by group_index.
      Returns <0 on error, 0 on success. */
  int getSecurityGroup(unsigned int group_index, EDSGroupObject_ptr & out_group);

  /** Returns (in out_group argument) technological group identified by group_index.
      Returns <0 on error, 0 on success. */
  int getTechGroup(unsigned int group_index, EDSGroupObject_ptr & out_group);

  /** Changes name and description of security group identified by group_index.
      Returns <0 on error, 0 on success. */
  int alterSecurityGroup(unsigned int group_index,
    const char * name, const char * desc);

  /** Changes name and description of technological group identified by group_index.
      Returns <0 on error, 0 on success. */
  int alterTechGroup(unsigned int group_index,
    const char * name, const char * desc);

  /** Allocates new source object by copying data from passed parameters.
      Returns null pointer on error. */
  EDSGlobalSource_ptr newSource(unsigned int id, const char * name,
                                const char * desc, const char * host,
                                const char * p_pref, const char * p_post,
                                const EDSGroups & sg, const EDSGroups & tg,
                                ObjEDSSourceKind kind, unsigned int options);

  /** Returns number of sources, or <0 on error. */
  int getSourceCount();

  /** Returns 1 if sources have changed since last synchronization,
      0 if not, <0 on error. */
  int sourcesChanged();

  /** Returns (in out_source argument) source identified by its index.
      Returns <0 on error, 0 on success. */
  int getSourceByIndex(unsigned int source_index, EDSGlobalSource_ptr & out_source);

  /** Returns (in out_source argument) source identified by its id.
      Returns <0 on error, 0 on success. */
  int getSourceById(unsigned int source_id, EDSGlobalSource_ptr & out_source);

  /** Creates source using data from source argument.
      Returns <0 on error, 0 on success. */
  int createSource(const EDSGlobalSource & source);

  /** Changes source identified by its index (source_index) using data from
      source argument. Returns <0 on error, 0 on success. */
  int alterSource(unsigned int source_index, const EDSGlobalSource & source);

  /** Removes source identified by source_index.
      Returns <0 on error, 0 on success. */
  int removeSource(unsigned int source_index);

  /** Allocates new global object by copying data from passed parameters.
      Returns null pointer on error. */
  EDSGlobalObject_ptr newGlobalObject(unsigned int source_id, const char * file,
                                      const char * name, unsigned long data_ts,
                                      const EDSGroups & sg, const EDSGroups & tg,
                                      const EDSMd5 & md5);

  /** Returns 1 if global objects have changed since last synchronization,
      0 if not, <0 on error. */
  int globalObjectsChanged();

  /** Returns number of global objects, or <0 on error. */
  int getGlobalObjectCount();

  /** Returns (in out_global_obj argument) global object identified by its index.
      Returns <0 on error, 0 on success. */
  int getGlobalObjectByIndex(unsigned int global_obj_index,
                             EDSGlobalObject_ptr & out_global_obj);

  /** Returns (in out_global_obj argument) global object identified by its file name.
      Returns <0 on error, 0 on success. */
  int getGlobalObjectByFileName(unsigned int source_id, const char * file_name,
                                EDSGlobalObject_ptr & out_global_obj);

  /** Creates global object using data from global_obj argument.
      Returns <0 on error, 0 on success. */
  int createGlobalObject(const EDSGlobalObject & global_obj);

  /** Changes global object identified by its index (global_obj_index) using data from
      global_obj argument. Returns <0 on error, 0 on success. */
  int alterGlobalObject(unsigned int global_obj_index,
                        const EDSGlobalObject & global_obj);

  /** Removes global object identified by global_obj_index.
      Returns <0 on error, 0 on success. */
  int removeGlobalObject(unsigned int global_obj_index);

  /** Uploads contents of source_file to global object identified by global_obj_idx.
      Automatically updates md5 digest. Returns <0 on error, 0 on success. */
  int uploadGlobalObject(unsigned int global_obj_index,
                         const char * source_file);

  /** Downloads contents of global object identified by global_obj_idx to local file
      destination_file. Note that destination file will be truncated before download.
      Returns <0 on error, 0 on success. */
  int downloadGlobalObject(unsigned int global_obj_index,
                           const char * destination_file);

  /** Copies name of current user to buffer (up to buffer_size chars).
      Returns <0 on error, 0 on success. */
  int userName(std::string & userName);

  /** Fill sg parameter with SG of current user.
      Returns <0 on error, 0 on success. */
  int getCurrentUserSG(EDSGroups & sg);

  /** Returns 1 if current user is admin, 0 if not, <0 on error. */
  int isCurrentUserAdmin();

  /** Allocates new user object by copying data from passed parameters.
      Returns null pointer on error. */
  EDSUser_ptr newUser(const char * name, const char * desc,
                      const EDSGroups & sg, const char * auth_info,
                      bool locked);

  /** Returns 1 if users have changed since last synchronization,
      0 if not, <0 on error. */
  int usersChanged();

  /** Returns number of users, or <0 on error. */
  int getUserCount();

  /** Returns (in out_user argument) user identified by its index.
      Returns <0 on error, 0 on success. */
  int getUserByIndex(unsigned int user_index, EDSUser_ptr & out_user);

  /** Returns (in out_global_obj argument) global object identified by its name.
      Returns <0 on error, 0 on success. */
  int getUserByName(const char * name, EDSUser_ptr & out_user);

  /** Creates user. Returns <0 on error, 0 on success. */
  int createUser(const EDSUser & user);

  /** Imports user. Returns <0 on error, 0 on success. */
  int importUser(const EDSUser & user);

  /** Alters user. Returns <0 on error, 0 on success. */
  int alterUser(const EDSUser & user);

  /** Removes user. Returns <0 on error, 0 on success. */
  int removeUser(const char * user_name);

  /** Returns 1 if current user can access specified object,
      0 if not, <0 on error. */
  int mayCurrentUserAccessObject(const char * source_name,
                                 const char * object_name );

  /** Fills sg parameter with SG of specified user.
      Returns <0 on error, 0 on success. */
  int getUserSG(const char * user_name, EDSGroups & sg);

  /** Returns 1 if specified user belongs to group (specified by name),
      0 if not, <0 on error. */
  int userBelongsToSGByName(const char * user_name, const char * group_name);

  /** Returns 1 if specified user belongs to group (specified by index),
      0 if not, <0 on error. */
  int userBelongsToSGByIndex(const char * user_name, unsigned int group_index);

  /** Returns 1 if user is admin, 0 if not, <0 on error. */
  int isUserAdmin(const char * user_name);

  /** Allocates new task object by copying data from passed parameters.
      Returns null pointer on error. */
  EDSTask_ptr newTask(unsigned int ref_task_idx,
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
                      unsigned int retries);

  /** Returns 1 if global tasks have changed since last synchronization,
      0 if not, <0 on error. */
  int tasksChanged();

  /** Creates task. Returns <0 on error, 0 on success. */
  int createTask(const EDSTask & task);

  /** Alters task. Returns <0 on error, 0 on success. */
  int alterTask(unsigned int task_index, const EDSTask & task);

  /** Removes task. Returns <0 on error, 0 on success. */
  int removeTask(unsigned int task_index);

  /** Returns (in out_task argument) task identified by its index.
      Returns <0 on error, 0 on success. */
  int getTaskByIndex(unsigned int task_index, EDSTask_ptr & out_task);

  /** Returns (in out_task argument) task identified by its id.
      Returns <0 on error, 0 on success. */
  int getTaskById(unsigned int task_id, EDSTask_ptr & out_task);

  /** Returns number of tasks, or <0 on error. */
  int getTaskCount();

 private:
  ObjEDS(const ObjEDS&);
  ObjEDS &operator =(const ObjEDS&);

  ObjEDSLib * lib;
  p_ObjEDSConnection conn;
#ifdef WIN32
  HANDLE lib_handle;
#else
  void * lib_handle;
#endif
};

#endif //_OBJEDS_H_
