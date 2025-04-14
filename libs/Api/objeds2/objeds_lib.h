// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

/*
 * file:	objeds_lib.h
 * project:	ESSII
 * module:	API
 */

#ifndef _OBJEDS_LIB_H_
#define _OBJEDS_LIB_H_

#if defined(__CPPLUS) || defined(__CPLUSPLUS) || defined(__cplusplus)
extern "C"
{
#endif

#if defined(_WIN32) || defined(__WIN32__) || defined(ESS_WIN32)
#define ExternalDecl __declspec(dllexport)
#else
#define ExternalDecl
#endif

#define OBJ_EDS_MAX_GROUPS 256

#define OBJ_EDS_SUCCESS               0
#define OBJ_EDS_BAD_CONNECTION_OBJECT -300
#define OBJ_EDS_INIT_FAILED           -301
#define OBJ_EDS_NO_CONNECTION         -302
#define OBJ_EDS_LOGIN_DENIED          -303
#define OBJ_EDS_PROTOCOL_MISMATCH     -304
#define OBJ_EDS_UNKNOWN_USER          -305
#define OBJ_EDS_BAD_PARAMS            -306
#define OBJ_EDS_OPERATION_FAILED      -307
#define OBJ_EDS_OPERATION_TIMED_OUT   -308
#define OBJ_EDS_INDEX_OUT_OF_BOUNDS   -309
#define OBJ_EDS_FILE_ACCESS_ERROR     -310

#define OBJ_EDS_ERR_INDEX ((unsigned int)-1)
#define OBJ_EDS_NEW_INDEX ((unsigned int)-2)

  /** Structure that represents connection to EDS Obj Server*/
  struct s_ObjEDSConnection;
  typedef struct s_ObjEDSConnection * p_ObjEDSConnection;

  /** Allocates new connection object. Always free returned object
      using ObjEDSDestroyConnection. Returns null pointer on error. */
  typedef p_ObjEDSConnection (*ObjEDSNewConnection)();

  /** Destroy connection object and its internal data. */
  typedef void (*ObjEDSDestroyConnection)(p_ObjEDSConnection conn);

  /** Initializes connection structure using parameters:
      local host, local port,
      remote host, remote port,
      user, password,
      port range, max packet size. */
  typedef int (*ObjEDSInit)(p_ObjEDSConnection conn,
                            const char * lhost, int lport,
                            const char * rhost, int rport,
                            const char * user, const char * password,
                            int lport_range, int max_packet);
  /** Shuts connection to EDS Server */
  typedef void (*ObjEDSShut)(p_ObjEDSConnection conn);
  /** Setups logger using setup string.
      For example: str="debug=7 logger=console:7 subsystems=ALL"*/
  typedef void (*ObjEDSSetupLogger)(const char * str);

  /** Synchronizes with ObjServer. This call also updates state flags.
      Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSSynchronize)(p_ObjEDSConnection conn);

  /** Flushes object cache. Returns 0 on success, <0 on error. */
  typedef int (*ObjEDSFlushGlobalCacheFile)(p_ObjEDSConnection conn);

  /** Structure that represents group object.
      It is created by ObjEDSGetSecurityGroup and ObjEDSGetTechGroup.
      Always free instances of this structure using ObjEDSDestroyGroupObject. */
  typedef struct
  {
    unsigned int index;
    char * name;
    char * desc;
  } s_ObjEDSGroupObject;
  typedef s_ObjEDSGroupObject * p_ObjEDSGroupObject;

  /** Returns 1 if groups have changed since last synchronization,
      0 if not, <0 on error. */
  typedef int (*ObjEDSGroupsChanged)(p_ObjEDSConnection conn);

  /** Returns (in out_group argument) security group identified by group_index.
      Note that structure returned in out_group must be freed using
      ObjEDSDestroyGroupObject function. Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSGetSecurityGroup)(p_ObjEDSConnection conn,
                                        unsigned int group_index,
                                        p_ObjEDSGroupObject * out_group);

  /** Returns (in out_group argument) technological group identified by group_index.
      Note that structure returned in out_group must be freed using
      ObjEDSDestroyGroupObject function. Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSGetTechGroup)(p_ObjEDSConnection conn,
                                    unsigned int group_index,
                                    p_ObjEDSGroupObject * out_group);

  /** Changes name and description of security group identified by group_index.
      Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSAlterSecurityGroup)(p_ObjEDSConnection conn,
                                          unsigned int group_index,
                                          const char * name,
                                          const char * desc);

  /** Changes name and description of technological group identified by group_index.
      Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSAlterTechGroup)(p_ObjEDSConnection conn,
                                      unsigned int group_index,
                                      const char * name,
                                      const char * desc);

  /** Destroys group object and its internal data. */
  typedef void (*ObjEDSDestroyGroupObject)(p_ObjEDSGroupObject group);

  /** Array of groups (flag) */
  typedef unsigned char ObjEDSGroups[OBJ_EDS_MAX_GROUPS / 8];

  /**
     Defines kinds of sources.
  */
  typedef enum
  {
    ObjEDSSourceKindDisk = 0,
    ObjEDSSourceKindFtp,
    ObjEDSSourceKindDb,
  } ObjEDSSourceKind;

  /**
     Defines source options.
  */
  typedef enum
  {
    ObjEDSSourceOptionFullPointName = 0x00000001,
  } ObjEDSSourceOption;

  /** Structure that represents source object.
      Create new instances of this structure using ObjEDSNewSource.
      Always free these structures using ObjEDSDestroySource. */
  typedef struct
  {
    unsigned int id;
    char * name;
    char * desc;
    char * host;
    char * p_pref;
    char * p_post;
    ObjEDSGroups sg;
    ObjEDSGroups tg;
    ObjEDSSourceKind kind;
    unsigned int options;
  } s_ObjEDSGlobalSource;
  typedef s_ObjEDSGlobalSource * p_ObjEDSGlobalSource;

  /** Allocates new source object by copying data from passed parameters.
      Always free returned object using ObjEDSDestroySource.
      Returns 0 on error. */
  typedef p_ObjEDSGlobalSource (*ObjEDSNewSource)(unsigned int id,
                                                  const char * name,
                                                  const char * desc,
                                                  const char * host,
                                                  const char * p_pref,
                                                  const char * p_post,
                                                  const ObjEDSGroups sg,
                                                  const ObjEDSGroups tg,
                                                  ObjEDSSourceKind kind,
                                                  unsigned int options);

  /** Destroys global source object and its internal data. */
  typedef void (*ObjEDSDestroySource)(p_ObjEDSGlobalSource source);

  /** Returns 1 if sources have changed since last synchronization,
      0 if not, <0 on error. */
  typedef int (*ObjEDSSourcesChanged)(p_ObjEDSConnection conn);

  /** Returns number of sources, or <0 on error. */
  typedef int (*ObjEDSGetSourceCount)(p_ObjEDSConnection conn);

  /** Returns (in out_source argument) source identified by its index.
      Note that structure returned in out_source must be freed using
      ObjEDSDestroySourceObject function. Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSGetSourceByIndex)(p_ObjEDSConnection conn,
                                        unsigned int source_index,
                                        p_ObjEDSGlobalSource * out_source);

  /** Returns (in out_source argument) source identified by its id.
      Note that structure returned in out_source must be freed using
      ObjEDSDestroySourceObject function. Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSGetSourceById)(p_ObjEDSConnection conn,
                                     unsigned int source_id,
                                     p_ObjEDSGlobalSource * out_source);

  /** Creates source using data from source argument.
      It is user's responsibility to destroy source object.
      Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSCreateSource)(p_ObjEDSConnection conn,
                                    p_ObjEDSGlobalSource source);

  /** Changes source identified by its index (source_index) using data from
      source argument. It is user's responsibility to destroy source object.
      Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSAlterSource)(p_ObjEDSConnection conn,
                                   unsigned int source_index,
                                   p_ObjEDSGlobalSource source);

  /** Removes source identified by source_index.
      Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSRemoveSource)(p_ObjEDSConnection conn,
                                    unsigned int source_index);

  typedef unsigned char ObjEDSMd5[16];

  /** Structure that represents global object.
      Create new instances of this structure using ObjEDSNewGlobalObject.
      Always free these structures using ObjEDSDestroyGlobalObject. */
  typedef struct
  {
    unsigned int source_id;
    char * file;
    char * name;
    unsigned long data_ts;
    ObjEDSGroups sg;
    ObjEDSGroups tg;
    ObjEDSMd5 md5;
  } s_ObjEDSGlobalObject;
  typedef s_ObjEDSGlobalObject * p_ObjEDSGlobalObject;

  /** Allocates new global object by copying data from passed parameters.
      Always free returned object using ObjEDSDestroyGlobalObject.
      Returns 0 on error. */
  typedef p_ObjEDSGlobalObject (*ObjEDSNewGlobalObject)(unsigned int source_id,
                                                        const char * file,
                                                        const char * name,
                                                        unsigned long data_ts,
                                                        const ObjEDSGroups sg,
                                                        const ObjEDSGroups tg,
                                                        const ObjEDSMd5 md5);

  /** Destroys global object and its internal data. */
  typedef void (*ObjEDSDestroyGlobalObject)(p_ObjEDSGlobalObject global_obj);

  /** Returns 1 if global objects have changed since last synchronization,
      0 if not, <0 on error. */
  typedef int (*ObjEDSGlobalObjectsChanged)(p_ObjEDSConnection conn);

  /** Returns number of global objects, or <0 on error. */
  typedef int (*ObjEDSGetGlobalObjectCount)(p_ObjEDSConnection conn);

  /** Returns (in out_global_obj argument) global object identified by its index.
      Note that structure returned in out_global_obj must be freed using
      ObjEDSDestroyGlobalObject function. Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSGetGlobalObjectByIndex)(p_ObjEDSConnection conn,
                                              unsigned int global_obj_index,
                                              p_ObjEDSGlobalObject * out_global_obj);

  /** Returns (in out_global_obj argument) global object identified by its file name.
      Note that structure returned in out_global_obj must be freed using
      ObjEDSDestroyGlobalObject function. Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSGetGlobalObjectByFileName)(p_ObjEDSConnection conn,
                                                 unsigned int source_id,
                                                 const char * file_name,
                                                 p_ObjEDSGlobalObject * out_global_obj);

  /** Create global object using data from global_obj argument.
      It is user's responsibility to destroy global_obj.
      Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSCreateGlobalObject)(p_ObjEDSConnection conn,
                                          p_ObjEDSGlobalObject global_obj);

  /** Changes global object identified by its index (global_obj_index) using data from
      global_obj argument. It is user's responsibility to destroy global_obj.
      Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSAlterGlobalObject)(p_ObjEDSConnection conn,
                                         unsigned int global_obj_index,
                                         p_ObjEDSGlobalObject global_obj);

  /** Removes global object identified by global_obj_index.
      Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSRemoveGlobalObject)(p_ObjEDSConnection conn,
                                          unsigned int global_obj_index);

  /** Uploads contents of source_file to global object identified by global_obj_idx.
      Automatically updates md5 digest.
      Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSUploadGlobalObject)(p_ObjEDSConnection conn,
                                          unsigned int global_obj_index,
                                          const char * source_file);

  /** Downloads contents of global object identified by global_obj_idx to local file
      destination_file. Note that destination file will be truncated before download.
      Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSDownloadGlobalObject)(p_ObjEDSConnection conn,
                                            unsigned int global_obj_index,
                                            const char * destination_file);

  /** Copies name of current user to buffer (up to buffer_size chars).
      Returns actual length of user name (including '\0'), or <0 on error. */
  typedef int (*ObjEDSUserName)(p_ObjEDSConnection conn,
                                char * buffer,
                                unsigned int buffer_size);

  /** Fill sg parameter with SG of current user.
      Returns 0 on success, <0 on failure. */
  typedef int (*ObjEDSGetCurrentUserSG)(p_ObjEDSConnection conn,
                                        ObjEDSGroups sg);

  /** Returns 1 if current user is admin, 0 if not, <0 on error. */
  typedef int (*ObjEDSIsCurrentUserAdmin)(p_ObjEDSConnection conn);

  /** Structure that represents user.
      Create new instances of this structure using ObjEDSNewUser.
      Always free these structures using ObjEDSDestroyUser. */
  typedef struct
  {
    char * name;
    char * desc;
    ObjEDSGroups sg;
    char * auth_info;
    int locked;
  } s_ObjEDSUser;
  typedef s_ObjEDSUser * p_ObjEDSUser;

  /** Allocates new user object by copying data from passed parameters.
      Always free returned object using ObjEDSDestroyUser.
      Returns 0 on error. */
  typedef p_ObjEDSUser (*ObjEDSNewUser)(const char * name, const char * desc,
                                        const ObjEDSGroups sg,
                                        const char * auth_info, int locked);

  /** Destroys user object and its internal data. */
  typedef void (*ObjEDSDestroyUser)(p_ObjEDSUser user);

  /** Returns 1 if users have changed since last synchronization,
      0 if not, <0 on error. */
  typedef int (*ObjEDSUsersChanged)(p_ObjEDSConnection conn);

  /** Returns number of users, or <0 on error. */
  typedef int (*ObjEDSGetUserCount)(p_ObjEDSConnection conn);

  /** Returns (in out_user argument) user identified by its index.
      Note that structure returned in out_user must be freed using
      ObjEDSDestroyUser function. Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSGetUserByIndex)(p_ObjEDSConnection conn,
                                      unsigned int user_index,
                                      p_ObjEDSUser * out_user);

  /** Returns (in out_global_obj argument) global object identified by its name.
      Note that structure returned in out_global_obj must be freed using
      ObjEDSDestroyUser function. Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSGetUserByName)(p_ObjEDSConnection conn,
                                     const char * name,
                                     p_ObjEDSUser * out_user);

  /** Creates user. Returns 0 on success, <0 on failure. */
  typedef int (*ObjEDSCreateUser)(p_ObjEDSConnection conn,
                                  p_ObjEDSUser user);

  /** Imports user. Returns 0 on success, <0 on failure. */
  typedef int (*ObjEDSImportUser)(p_ObjEDSConnection conn,
                                  p_ObjEDSUser user);

  /** Alters user. Returns 0 on success, <0 on failure. */
  typedef int (*ObjEDSAlterUser)(p_ObjEDSConnection conn,
                                  p_ObjEDSUser user);

  /** Removes user. Returns 0 on success, <0 on failure. */
  typedef int (*ObjEDSRemoveUser)(p_ObjEDSConnection conn,
                                  const char * user_name);

  /** Returns 1 if current user can access specified object,
      0 if not, <0 on error. */
  typedef int (*ObjEDSMayCurrentUserAccessObject)(p_ObjEDSConnection conn,
                                                  const char * source_name,
                                                  const char * object_name );

  /** Fills sg parameter with SG of specified user.
      Returns 0 on success, <0 on failure. */
  typedef int (*ObjEDSGetUserSG)(p_ObjEDSConnection conn,
                                 const char * user_name,
                                 ObjEDSGroups sg);

  /** Returns 1 if specified user belongs to group (specified by name),
      0 if not, <0 on error. */
  typedef int (*ObjEDSUserBelongsToSGByName)(p_ObjEDSConnection conn,
                                             const char * user_name,
                                             const char * group_name);

  /** Returns 1 if specified user belongs to group (specified by index),
      0 if not, <0 on error. */
  typedef int (*ObjEDSUserBelongsToSGByIndex)(p_ObjEDSConnection conn,
                                              const char * user_name,
                                              unsigned int group_index);

  /** Returns 1 if user is admin, 0 if not, <0 on error. */
  typedef int (*ObjEDSIsUserAdmin)(p_ObjEDSConnection conn,
                                   const char * user_name);

  typedef enum
  {
    ObjEDSTaskStatusCreated = 0,
    ObjEDSTaskStatusRunning,
    ObjEDSTaskStatusFinished,
    ObjEDSTaskStatusCancelled,
    ObjEDSTaskStatusZombie,
  } ObjEDSTaskStatus;

  typedef enum 
  {
    ObjEDSTaskPriorityLow = 0,
    ObjEDSTaskPriorityNormal,
    ObjEDSTaskPriorityHigh,
  } ObjEDSTaskPriority;

  /** Structure that represents task object.
      Create new instances of this structure using ObjEDSNewTask.
      Always free these structures using ObjEDSDestroyTask. */
  typedef struct
  {
      unsigned int ref_task_idx;
      unsigned int ref_ts;
      unsigned int run_ts;
      int run_delay;
      const char * type;
      ObjEDSTaskPriority priority;
      const char * params;
      ObjEDSTaskStatus status;
      unsigned int task_ts;
      unsigned int task_usec;
      unsigned int finished;
      unsigned int retries;
  } s_ObjEDSTask;
  
  typedef s_ObjEDSTask * p_ObjEDSTask;

  /** Allocates new task object by copying data from passed parameters.
      Always free returned object using ObjEDSDestroyTask.
      Returns 0 on error. */
  typedef p_ObjEDSTask (*ObjEDSNewTask)(unsigned int ref_task_idx,
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

  /** Destroys global task object and its internal data. */
  typedef void (*ObjEDSDestroyTask)(p_ObjEDSTask task);

  /** Returns 1 if tasks have changed since last synchronization,
      0 if not, <0 on error. */
  typedef int (*ObjEDSTasksChanged)(p_ObjEDSConnection conn);

    /** Creates task using data from task argument.
      It is user's responsibility to destroy task object.
      Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSCreateTask)(p_ObjEDSConnection conn,
                                   p_ObjEDSTask task);


  /** Returns (in out_task argument) task identified by its index.
      Note that structure returned in out_task must be freed using
      ObjEDSDestroyTask function. Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSGetTaskByIndex)(p_ObjEDSConnection conn,
                                       unsigned int task_index,
                                       p_ObjEDSTask * out_task);

  /** Returns (in out_task argument) task identified by its id.
      Note that structure returned in out_task must be freed using
      ObjEDSDestroyTask function. Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSGetTaskById)(p_ObjEDSConnection conn,
                                    unsigned int task_id,
                                    p_ObjEDSTask * out_task);


  /** Returns number of tasks, or <0 on error. */
  typedef int (*ObjEDSGetTaskCount)(p_ObjEDSConnection conn);

  /** Changes task identified by its index (task_index) using data from
      task argument. It is user's responsibility to destroy task object.
      Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSAlterTask)(p_ObjEDSConnection conn,
                                  unsigned int task_index,
                                  p_ObjEDSTask task);

  /** Removes task identified by task_index.
      Returns <0 on error, 0 on success. */
  typedef int (*ObjEDSRemoveTask)(p_ObjEDSConnection conn,
                                   unsigned int task_index);

  /** Structure containing all library functions. If returned by
      getObjEDSLib it contains proper pointers. All functions can be
      accesed in library using same names as this structure fields*/
  typedef struct
  {
    ObjEDSNewConnection newConnection;
    ObjEDSDestroyConnection destroyConnection;
    ObjEDSInit init;
    ObjEDSShut shut;
    ObjEDSSetupLogger setupLogger;
    ObjEDSSynchronize synchronize;
    ObjEDSFlushGlobalCacheFile flushGlobalCacheFile;
    ObjEDSGroupsChanged groupsChanged;
    ObjEDSGetSecurityGroup getSecurityGroup;
    ObjEDSGetTechGroup getTechGroup;
    ObjEDSAlterSecurityGroup alterSecurityGroup;
    ObjEDSAlterTechGroup alterTechGroup;
    ObjEDSDestroyGroupObject destroyGroupObject;
    ObjEDSNewSource newSource;
    ObjEDSDestroySource destroySource;
    ObjEDSSourcesChanged sourcesChanged;
    ObjEDSGetSourceCount getSourceCount;
    ObjEDSGetSourceByIndex getSourceByIndex;
    ObjEDSGetSourceById getSourceById;
    ObjEDSCreateSource createSource;
    ObjEDSAlterSource alterSource;
    ObjEDSRemoveSource removeSource;
    ObjEDSNewGlobalObject newGlobalObject;
    ObjEDSDestroyGlobalObject destroyGlobalObject;
    ObjEDSGlobalObjectsChanged globalObjectsChanged;
    ObjEDSGetGlobalObjectCount getGlobalObjectCount;
    ObjEDSGetGlobalObjectByIndex getGlobalObjectByIndex;
    ObjEDSGetGlobalObjectByFileName getGlobalObjectByFileName;
    ObjEDSCreateGlobalObject createGlobalObject;
    ObjEDSAlterGlobalObject alterGlobalObject;
    ObjEDSRemoveGlobalObject removeGlobalObject;
    ObjEDSUploadGlobalObject uploadGlobalObject;
    ObjEDSDownloadGlobalObject downloadGlobalObject;
    ObjEDSUserName userName;
    ObjEDSGetCurrentUserSG getCurrentUserSG;
    ObjEDSIsCurrentUserAdmin isCurrentUserAdmin;
    ObjEDSNewUser newUser;
    ObjEDSDestroyUser destroyUser;
    ObjEDSUsersChanged usersChanged;
    ObjEDSGetUserCount getUserCount;
    ObjEDSGetUserByIndex getUserByIndex;
    ObjEDSGetUserByName getUserByName;
    ObjEDSCreateUser createUser;
    ObjEDSImportUser importUser;
    ObjEDSAlterUser alterUser;
    ObjEDSRemoveUser removeUser;
    ObjEDSMayCurrentUserAccessObject mayCurrentUserAccessObject;
    ObjEDSGetUserSG getUserSG;
    ObjEDSUserBelongsToSGByName userBelongsToSGByName;
    ObjEDSUserBelongsToSGByIndex userBelongsToSGByIndex;
    ObjEDSIsUserAdmin isUserAdmin;
    ObjEDSNewTask newTask;
    ObjEDSDestroyTask destroyTask;
    ObjEDSTasksChanged tasksChanged;
    ObjEDSCreateTask createTask;
    ObjEDSAlterTask alterTask;
    ObjEDSRemoveTask removeTask;
    ObjEDSGetTaskByIndex getTaskByIndex;
    ObjEDSGetTaskById getTaskById;
    ObjEDSGetTaskCount getTaskCount;
  } ObjEDSLib;

/* This version should be manually updated after changes in library iface */
#define OBJ_EDS_LIB_VERSION    "9.1 OBJ_API=1"

  /** Returns fully initialized ObjEDSLib static pointer (it
      shouldn't be destroyed)*/
  typedef ObjEDSLib* (*GetObjEDSLib)(const char * version);

#if defined(__CPPLUS) || defined(__CPLUSPLUS) || defined(__cplusplus)
} // extern "C"
#endif

#endif //_OBJEDS_LIB_H_
