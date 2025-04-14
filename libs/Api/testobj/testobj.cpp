// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

#include <stdlib.h>
#include <stdio.h>
#include <time.h>
#if !defined(ESS_WIN32) && !defined(ESS_CYGWIN)
#include <math.h>
#endif

//#include "../liveeds2/liveeds.h"
#include "../objeds2/objeds.h"

//#include "../liveeds2/liveeds.cpp"
#include "../objeds2/objeds.cpp"

void ess_sleep( float f )
{
#ifdef ESS_WIN32
  DWORD t;

  t = static_cast<DWORD>(f * 1000.0);
  Sleep(t);
#elif defined(ESS_CYGWIN)
  unsigned long t;

  t = static_cast<unsigned long>(f * 1e6);
  usleep(t);
#else
  struct timespec t;

  t.tv_sec = static_cast<time_t>(floor(f));
  t.tv_nsec = static_cast<long>((f - floor(f)) * 1000000000.0);
  nanosleep(&t, NULL);
#endif
}

void eds_test_groups(ObjEDS* connection)
{
  int err = connection->groupsChanged();
  printf("groupsChanged() returned %d\n", err);

  EDSGroupObject_ptr groupObj;
  err = connection->getSecurityGroup(1, groupObj);
  printf("getSecurityGroup() returned %d\n", err);
  printf("%d %s %s\n", groupObj->index(), groupObj->name(), groupObj->desc());

  err = connection->getTechGroup(255, groupObj);
  printf("getTechGroup() returned %d\n", err);
  printf("%d %s %s\n", groupObj->index(), groupObj->name(), groupObj->desc());

  err = connection->alterSecurityGroup(130, "test_group", "Test group description");
  printf("alterSecurityGroup() returned %d\n", err);

  err = connection->alterTechGroup(131, "test_group", "Test group description");
  printf("alterTechGroup() returned %d\n", err);
}

void eds_test_sources(ObjEDS * connection)
{
  EDSGroups sg, tg;
  sg.setPermission(0, true);
  sg.setPermission(100, true);
  sg.setPermission(255, true);
  tg.setPermission(0, true);
  tg.setPermission(100, true);
  tg.setPermission(255, true);

  int err = connection->sourcesChanged();
  printf("sourcesChanged() returned %d\n", err);

  EDSGlobalSource_ptr globSrc = connection->newSource(
    OBJ_EDS_NEW_INDEX, "test_source", "test source description", "127.0.0.1",
    "ppref", "ppost", sg, tg, ObjEDSSourceKindDisk,
    ObjEDSSourceOptionFullPointName);
  printf("newSource() returned %s\n", globSrc.get() ? "source" : "null");

  err = connection->createSource(*globSrc);
  printf("createSource() returned %d\n", err);

  if (err >= 0)
  {
    int srcCount = connection->getSourceCount();
    printf("getSourceCount() returned %d\n", srcCount);

    err = connection->getSourceByIndex(srcCount - 1, globSrc);
    printf("getSourceByIndex() returned %d\n", err);

    err = connection->getSourceById(globSrc->id(), globSrc);
    printf("getSourceById() returned %d\n", err);

    sg = globSrc->sg();
    tg = globSrc->tg();
    sg.setPermission(255, false);
    tg.setPermission(255, false);
    // note that id cannot be altered
    EDSGlobalSource_ptr alterGlobSrc = connection->newSource(
      globSrc->id(), "test_source1", "test source description1", "127.0.0.2",
      "ppref1", "ppost1", sg, tg, ObjEDSSourceKindDisk,
      ObjEDSSourceOptionFullPointName);
    err = connection->alterSource(srcCount - 1, *alterGlobSrc);
    printf("alterSource() returned %d\n", err);

    err = connection->removeSource(srcCount - 1);
    printf("removeSource() returned %d\n", err);
  }
}

void eds_test_global_objects(ObjEDS * connection)
{
  EDSGroups sg, tg;
  sg.setPermission(0, true);
  sg.setPermission(100, true);
  sg.setPermission(255, true);
  tg.setPermission(0, true);
  tg.setPermission(100, true);
  tg.setPermission(255, true);

  EDSMd5 md5;

  int err = connection->globalObjectsChanged();
  printf("globalObjectsChanged() returned %d\n", err);

  EDSGlobalSource_ptr globSrc;
  int srcCount = connection->getSourceCount();
  if (srcCount <= 0)
    return;
  err = connection->getSourceByIndex(0, globSrc);
  if (err < 0)
    return;
  unsigned int sourceId = globSrc->id();

  EDSGlobalObject_ptr globObj = connection->newGlobalObject(
    sourceId,
    "_readme_.txt",
    "test object description",
    static_cast<unsigned long>(time(NULL)),
    sg,
    tg,
    md5);

  printf(
    "newGlobalObject() returned %s\n",
    globObj.get() ? "global object" : "null");

  err = connection->createGlobalObject(*globObj);
  printf("createGlobalObject() returned %d\n", err);

  if (err >= 0)
  {
    int objCount = connection->getGlobalObjectCount();
    printf("getGlobalObjectCount() returned %d\n", objCount);

    err = connection->getGlobalObjectByIndex(objCount - 1, globObj);
    printf("getGlobalObjectByIndex() returned %d\n", err);

    err = connection->getGlobalObjectByFileName(globObj->sourceId(),
      globObj->file(), globObj);
    printf("getGlobalObjectByFileName() returned %d\n", err);

    sg = globObj->sg();
    tg = globObj->tg();
    sg.setPermission(255, false);
    tg.setPermission(255, false);
    // note that source id and file cannot be altered
    EDSGlobalObject_ptr alterGlobObj = connection->newGlobalObject(
      globObj->sourceId(), globObj->file(), "test object description1",
      globObj->dataTS() + 1, sg, tg, globObj->md5());
    err = connection->alterGlobalObject(objCount - 1, *alterGlobObj);
    printf("alterGlobalObject() returned %d\n", err);

    err = connection->uploadGlobalObject(objCount - 1, "test_file_orig");
    printf("uploadGlobalObject() returned %d\n", err);

    err = connection->downloadGlobalObject(objCount - 1, "test_file_downloaded");
    printf("downloadGlobalObject() returned %d\n", err);

    err = connection->removeGlobalObject(objCount - 1);
    printf("removeGlobalObject() returned %d\n", err);
  }
}

void eds_test_current_user(ObjEDS * connection)
{
  std::string userName;
  int err = connection->userName(userName);
  printf("userName() returned %d\n", err);
  printf("%s\n", userName.c_str());

  EDSGroups groups;
  err = connection->getCurrentUserSG(groups);
  printf("getCurrentUserSG() returned %d\n", err);

  err = connection->isCurrentUserAdmin();
  printf("isCurrentUserAdmin() returned %d\n", err);

  err = connection->mayCurrentUserAccessObject("test", "test_test");
  printf("mayCurrentUserAccessObject() returned %d\n", err);
}

void eds_test_users(ObjEDS * connection)
{
  EDSGroups sg;
  sg.setPermission(0, true);
  sg.setPermission(100, true);
  sg.setPermission(255, true);

  int err = connection->usersChanged();
  printf("usersChanged() returned %d\n", err);

  EDSUser_ptr user = connection->newUser("test_user",
                                         "test user description",
                                         sg,
                                         "NULL:",
                                         false);
  printf("newUser() returned %s\n", user.get() ? "user" : "null");

  err = connection->createUser(*user);
  printf("createUser() returned %d\n", err);

  if (err >= 0)
  {
    int userCount = connection->getUserCount();
    printf("getUserCount() returned %d\n", userCount);

    err = connection->getUserByIndex(userCount - 1, user);
    printf("getUserByIndex() returned %d\n", err);

    err = connection->getUserByName(user->name(), user);
    printf("getUserByName() returned %d\n", err);

    sg = user->sg();
    sg.setPermission(255, false);
    // note that name cannot be altered
    EDSUser_ptr importUser = connection->newUser(
      user->name(), "test user description1", sg, "NULL:1", false);
    err = connection->importUser(*importUser);
    printf("importUser() returned %d\n", err);

    sg = user->sg();
    sg.setPermission(255, true);
    // note that name cannot be altered
    EDSUser_ptr alterUser = connection->newUser(
      user->name(), "test user description2", sg, "NULL:2", false);
    err = connection->alterUser(*alterUser);
    printf("alterUser() returned %d\n", err);

    err = connection->getUserSG("test_user", sg);
    printf("getUserSG() returned %d\n", err);

    err = connection->userBelongsToSGByName("test_user", "admin");
    printf("userBelongsToSGByName() returned %d\n", err);

    err = connection->userBelongsToSGByIndex("test_user", 255);
    printf("userBelongsToSGByIndex() returned %d\n", err);

    err = connection->isUserAdmin("test_user");
    printf("isUserAdmin() returned %d\n", err);

    err = connection->removeUser(user->name());
    printf("removeUser() returned %d\n", err);
  }
}

void eds_test_lib(const char * rhost, int rport)
{
  int err;
  ObjEDS * connection = new ObjEDS();

  //connection->setupLogger("");
  connection->setupLogger("debug=7 subsystems=ALL logger=console:7");

  err = connection->init("0.0.0.0", 0, rhost, rport,
                         "admin", "", 0, 32768);

  if (err != OBJ_EDS_SUCCESS)
  {
    printf("init() returned %d\n", err);
    return;
  }

  connection->flushGlobalCacheFile();

  err = connection->synchronize();
  if (err != OBJ_EDS_SUCCESS)
  {
    printf("synchronize() returned %d\n", err);
    return;
  }

  eds_test_groups(connection);
  eds_test_sources(connection);
  eds_test_global_objects(connection);
  eds_test_current_user(connection);
  eds_test_users(connection);
}

int main(int argc, char** argv)
{
  if(argc!=3) {
    printf("Usage: %s rhost rport\n", argv[0] );
    return 1;
  }

  printf(">>>>>>>>>>>>> TO START TEST PRESS ENTER <<<<<<<<<<<<\n");
  //getchar();

  eds_test_lib(argv[1],atoi(argv[2]));

  return 0;
}
