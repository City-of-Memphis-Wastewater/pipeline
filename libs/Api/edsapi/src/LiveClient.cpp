// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

#include "../include/LiveClient.h"

#include <iostream>
#include <ctype.h>
#include <memory>
#include <sstream>

#include "Backend.h"

using namespace eds;
using namespace eds::detail;

// types from eds namespace must be visible before
// LiveBackend.h is included
#include "LiveBackend.h"

namespace
{
llong convertToMicroSeconds(dword seconds, dword useconds)
{
  static const llong microSecondsInSecond = 1000000;

  return seconds * microSecondsInSecond + useconds;
}

llong convertToSeconds(dword seconds, dword useconds)
{
  static const llong halfOfSecondInMicroseconds = 500000;

  if (useconds < halfOfSecondInMicroseconds)
    return seconds;

  return seconds + 1;
}
} // namespace


namespace eds
{

namespace live
{

template <typename FunctionPtr>
struct Function
{
  Function() : ptr(0) {}

  bool isSupportedByBackend() const { return ptr != 0; }

  FunctionPtr ptr;
  std::string functionName;
  std::string exportName;
};

struct FunctionTable
{
  Function<EDSLiveInitPtr> init;
  Function<EDSLiveInitializeAsAgentPtr> initializeAsAgent;
  Function<EDSLiveInitializeAsUserPtr> initializeAsUser;
  Function<EDSLiveSetupLoggerPtr> setupLogger;
  Function<EDSLiveFindByIESSPtr> findByIESS;
  Function<EDSLiveFindByIESSNoCasePtr> findByIESSNoCase;
  Function<EDSLiveFindByIDCSPtr> findByIDCS;
  Function<EDSLiveFindByIDCSNoCasePtr> findByIDCSNoCase;
  Function<EDSLiveSetInputPtr> setInput;
  Function<EDSLiveSetOutputPtr> setOutput;
  Function<EDSLiveUnsetInputPtr> unsetInput;
  Function<EDSLiveUnsetOutputPtr> unsetOutput;
  Function<EDSLiveSynchronizeInputPtr> synchronizeInput;
  Function<EDSLiveReadAnalogPtr> readAnalog;
  Function<EDSLiveReadDoublePtr> readDouble;
  Function<EDSLiveReadPackedPtr> readPacked;
  Function<EDSLiveReadInt64Ptr> readInt64;
  Function<EDSLiveReadBinaryPtr> readBinary;
  Function<EDSLiveFieldIdFromNamePtr> fieldIdFromName;
  Function<EDSLiveFieldIdFromWDPFNamePtr> fieldIdFromWDPFName;
  Function<EDSLiveReadFieldIntPtr> readFieldInt;
  Function<EDSLiveReadFieldFloatPtr> readFieldFloat;
  Function<EDSLiveReadFieldDoublePtr> readFieldDouble;
  Function<EDSLiveReadFieldStringPtr> readFieldString;
  Function<EDSLiveReadFieldIntByNamePtr> readFieldIntByName;
  Function<EDSLiveReadFieldIntByWDPFNamePtr> readFieldIntByWDPFName;
  Function<EDSLiveReadFieldFloatByNamePtr> readFieldFloatByName;
  Function<EDSLiveReadFieldFloatByWDPFNamePtr> readFieldFloatByWDPFName;
  Function<EDSLiveReadFieldDoubleByNamePtr> readFieldDoubleByName;
  Function<EDSLiveReadFieldDoubleByWDPFNamePtr> readFieldDoubleByWDPFName;
  Function<EDSLiveReadFieldStringByNamePtr> readFieldStringByName;
  Function<EDSLiveReadFieldStringByWDPFNamePtr> readFieldStringByWDPFName;
  Function<EDSLiveReadATPtr> readAT;
  Function<EDSLiveWriteATPtr> writeAT;
  Function<EDSLiveWriteSTPtr> writeST;
  Function<EDSLiveWriteXSTnPtr> writeXSTn;
  Function<EDSLiveWriteAnalogPtr> writeAnalog;
  Function<EDSLiveWriteDoublePtr> writeDouble;
  Function<EDSLiveWritePackedPtr> writePacked;
  Function<EDSLiveWriteInt64Ptr> writeInt64;
  Function<EDSLiveWriteBinaryPtr> writeBinary;
  Function<EDSLiveSynchronizeOutputPtr> synchronizeOutput;
  Function<EDSLiveHighestLIDPtr> highestLID;
  Function<EDSLivePointCountPtr> pointCount;
  Function<EDSLiveIsPointAlivePtr> isPointAlive;
  Function<EDSLivePointSIDPtr> pointSID;
  Function<EDSLivePointQualityPtr> pointQuality;
  Function<EDSLivePointIESSPtr> pointIESS;
  Function<EDSLivePointZDPtr> pointZD;
  Function<EDSLivePointIDCSPtr> pointIDCS;
  Function<EDSLivePointDESCPtr> pointDESC;
  Function<EDSLivePointAUXPtr> pointAUX;
  Function<EDSLivePointRTStringPtr> pointRTString;
  Function<EDSLivePointARPtr> pointAR;
  Function<EDSLivePointRTPtr> pointRT;
  Function<EDSLivePointValuePtr> pointValue;
  Function<EDSLiveIsUpdateRequiredPtr> isUpdateRequired;
  Function<EDSLiveStaticInfoChangedPtr> staticInfoChanged;
  Function<EDSLiveDynamicInfoChangedPtr> dynamicInfoChanged;
  Function<EDSLivePointSecGroupsPtr> pointSecGroups;
  Function<EDSLivePointTechGroupsPtr> pointTechGroups;
  Function<EDSLiveNewConnectionPtr> newConnection;
  Function<EDSLiveDestroyConnectionPtr> destroyConnection;
};


/** LiveClient **/

LiveClient::LiveClient(const char* version)
  : _backend(new Backend("live", version)),
    _connection(0)
{
  std::unique_ptr<FunctionTable> functions = std::make_unique<FunctionTable>();

#define EDSAPI_INITIALIZE_FUNCTION(functionName) \
  initializeFunction(functions->functionName, #functionName);

  EDSAPI_INITIALIZE_FUNCTION(init);
  EDSAPI_INITIALIZE_FUNCTION(initializeAsAgent);
  EDSAPI_INITIALIZE_FUNCTION(initializeAsUser);
  EDSAPI_INITIALIZE_FUNCTION(setupLogger);
  EDSAPI_INITIALIZE_FUNCTION(findByIESS);
  EDSAPI_INITIALIZE_FUNCTION(findByIESSNoCase);
  EDSAPI_INITIALIZE_FUNCTION(findByIDCS);
  EDSAPI_INITIALIZE_FUNCTION(findByIDCSNoCase);
  EDSAPI_INITIALIZE_FUNCTION(pointSID);
  EDSAPI_INITIALIZE_FUNCTION(setInput);
  EDSAPI_INITIALIZE_FUNCTION(setOutput);
  EDSAPI_INITIALIZE_FUNCTION(unsetInput);
  EDSAPI_INITIALIZE_FUNCTION(unsetOutput);
  EDSAPI_INITIALIZE_FUNCTION(synchronizeInput);
  EDSAPI_INITIALIZE_FUNCTION(readAnalog);
  EDSAPI_INITIALIZE_FUNCTION(readDouble);
  EDSAPI_INITIALIZE_FUNCTION(readPacked);
  EDSAPI_INITIALIZE_FUNCTION(readInt64);
  EDSAPI_INITIALIZE_FUNCTION(readBinary);
  EDSAPI_INITIALIZE_FUNCTION(fieldIdFromName);
  EDSAPI_INITIALIZE_FUNCTION(fieldIdFromWDPFName);
  EDSAPI_INITIALIZE_FUNCTION(readFieldInt);
  EDSAPI_INITIALIZE_FUNCTION(readFieldFloat);
  EDSAPI_INITIALIZE_FUNCTION(readFieldDouble);
  EDSAPI_INITIALIZE_FUNCTION(readFieldString);
  EDSAPI_INITIALIZE_FUNCTION(readFieldIntByName);
  EDSAPI_INITIALIZE_FUNCTION(readFieldIntByWDPFName);
  EDSAPI_INITIALIZE_FUNCTION(readFieldFloatByName);
  EDSAPI_INITIALIZE_FUNCTION(readFieldFloatByWDPFName);
  EDSAPI_INITIALIZE_FUNCTION(readFieldDoubleByName);
  EDSAPI_INITIALIZE_FUNCTION(readFieldDoubleByWDPFName);
  EDSAPI_INITIALIZE_FUNCTION(readFieldStringByName);
  EDSAPI_INITIALIZE_FUNCTION(readFieldStringByWDPFName);
  EDSAPI_INITIALIZE_FUNCTION(readAT);
  EDSAPI_INITIALIZE_FUNCTION(writeAT);
  EDSAPI_INITIALIZE_FUNCTION(writeST);
  EDSAPI_INITIALIZE_FUNCTION(writeXSTn);
  EDSAPI_INITIALIZE_FUNCTION(writeAnalog);
  EDSAPI_INITIALIZE_FUNCTION(writeDouble);
  EDSAPI_INITIALIZE_FUNCTION(writePacked);
  EDSAPI_INITIALIZE_FUNCTION(writeInt64);
  EDSAPI_INITIALIZE_FUNCTION(writeBinary);
  EDSAPI_INITIALIZE_FUNCTION(synchronizeOutput);
  EDSAPI_INITIALIZE_FUNCTION(highestLID);
  EDSAPI_INITIALIZE_FUNCTION(pointCount);
  EDSAPI_INITIALIZE_FUNCTION(isPointAlive);
  EDSAPI_INITIALIZE_FUNCTION(pointQuality);
  EDSAPI_INITIALIZE_FUNCTION(pointIESS);
  EDSAPI_INITIALIZE_FUNCTION(pointZD);
  EDSAPI_INITIALIZE_FUNCTION(pointIDCS);
  EDSAPI_INITIALIZE_FUNCTION(pointDESC);
  EDSAPI_INITIALIZE_FUNCTION(pointAUX);
  EDSAPI_INITIALIZE_FUNCTION(pointRTString);
  EDSAPI_INITIALIZE_FUNCTION(pointAR);
  EDSAPI_INITIALIZE_FUNCTION(pointRT);
  EDSAPI_INITIALIZE_FUNCTION(pointValue);
  EDSAPI_INITIALIZE_FUNCTION(isUpdateRequired);
  EDSAPI_INITIALIZE_FUNCTION(staticInfoChanged);
  EDSAPI_INITIALIZE_FUNCTION(dynamicInfoChanged);
  EDSAPI_INITIALIZE_FUNCTION(pointSecGroups);
  EDSAPI_INITIALIZE_FUNCTION(pointTechGroups);
  EDSAPI_INITIALIZE_FUNCTION(newConnection);
  EDSAPI_INITIALIZE_FUNCTION(destroyConnection);

#undef EDSAPI_INITIALIZE_FUNCTION

  checkFunction(functions->newConnection);

  _connection = functions->newConnection.ptr();
  if (_connection == 0)
    throw LiveClientError(LiveErrorCode_InvalidResult);

  _functions = functions.release();
}

LiveClient::~LiveClient()
{
  if (_connection != 0)
  {
    if (_functions->destroyConnection.ptr != 0)
      _functions->destroyConnection.ptr(_connection);
  }

  delete _functions;
  delete _backend;
}

void LiveClient::setupLogger(const char* str)
{
  checkFunction(_functions->setupLogger);

  _functions->setupLogger.ptr(str);
}

void LiveClient::init(int access_mode,
                      const char *lhost, eds::word lport,
                      const char *rhost, eds::word rport,
                      eds::word lport_range, eds::word max_packet)
{
  checkFunction(_functions->init);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->init.ptr(
    _connection, access_mode,
    lhost, lport, rhost, rport, lport_range, max_packet);
  if (result < 0)
    throw LiveClientError(result);
}

void LiveClient::initializeAsAgent(AccessMode access_mode,
                                   const char* program_name,
                                   const char* instance_name,
                                   const char* lhost,
                                   word lport,
                                   const char* rhost,
                                   word rport,
                                   word lport_range,
                                   word max_packet)
{
  if (!_functions->initializeAsAgent.isSupportedByBackend()
      && !_functions->init.isSupportedByBackend())
  {
    throwUnsupportedFunction(_functions->initializeAsAgent);
  }

  if (_connection == 0)
    throw UninitializedClientError();

  if (_functions->initializeAsAgent.isSupportedByBackend())
  {
    int result = _functions->initializeAsAgent.ptr(_connection,
                                                   access_mode,
                                                   program_name,
                                                   instance_name,
                                                   lhost,
                                                   lport,
                                                   rhost,
                                                   rport,
                                                   lport_range,
                                                   max_packet);
    if (result < 0)
      throw LiveClientError(result);
    return;
  }

  int result = _functions->init.ptr(
    _connection, access_mode, lhost, lport, rhost, rport, lport_range, max_packet);
  if (result < 0)
    throw LiveClientError(result);
}

void LiveClient::initializeAsUser(const char* user_name,
                                  const char* password,
                                  const char* lhost,
                                  word lport,
                                  const char* rhost,
                                  word rport,
                                  word lport_range,
                                  word max_packet)
{
  checkFunction(_functions->initializeAsUser);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->initializeAsUser.ptr(
    _connection, user_name, password, lhost, lport, rhost, rport, lport_range, max_packet);
  if (result < 0)
    throw LiveClientError(result);
}

void LiveClient::shut()
{
  checkFunction(_functions->destroyConnection);
  checkFunction(_functions->newConnection);

  if (_connection != 0)
    _functions->destroyConnection.ptr(_connection);

  _connection = _functions->newConnection.ptr();
  if (_connection == 0)
    throw LiveClientError(LiveErrorCode_InvalidResult);
}

int LiveClient::findByIESS(const char* iess)
{
  checkFunction(_functions->findByIESS);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->findByIESS.ptr(_connection, iess);
  if (result < 0 && result != -1)
    throw LiveClientError(result);

  return result;
}

int LiveClient::findByIESSNoCase(const char* iess)
{
  checkFunction(_functions->findByIESSNoCase);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->findByIESSNoCase.ptr(_connection, iess);
  if (result < 0 && result != -1)
    throw LiveClientError(result);

  return result;
}

int LiveClient::findByIDCS(const char* idcs, const char* zd)
{
  checkFunction(_functions->findByIDCS);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->findByIDCS.ptr(_connection, idcs, zd);
  if (result < 0 && result != -1)
    throw LiveClientError(result);

  return result;
}

int LiveClient::findByIDCSNoCase(const char* idcs, const char* zd)
{
  checkFunction(_functions->findByIDCSNoCase);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->findByIDCSNoCase.ptr(_connection, idcs, zd);
  if (result < 0 && result != -1)
    throw LiveClientError(result);

  return result;
}

int LiveClient::highestLID()
{
  checkFunction(_functions->highestLID);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->highestLID.ptr(_connection);
  if (result < 0)
    throw LiveClientError(result);

  return result;
}

int LiveClient::pointCount()
{
  checkFunction(_functions->pointCount);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->pointCount.ptr(_connection);
  if (result < 0)
    throw LiveClientError(result);

  return result;
}

bool LiveClient::isPointAlive(int lid)
{
  checkFunction(_functions->isPointAlive);

  if (_connection == 0)
    throw UninitializedClientError();

  return _functions->isPointAlive.ptr(_connection, lid);
}

void LiveClient::setInput(int lid)
{
  checkFunction(_functions->setInput);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->setInput.ptr(_connection, lid);
  if (result < 0)
    throw LiveClientError(result);
}

void LiveClient::setOutput(int lid)
{
  checkFunction(_functions->setOutput);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->setOutput.ptr(_connection, lid);
  if (result < 0)
    throw LiveClientError(result);
}

void LiveClient::unsetInput(int lid)
{
  checkFunction(_functions->unsetInput);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->unsetInput.ptr(_connection, lid);
  if (result < 0)
    throw LiveClientError(result);
}

void LiveClient::unsetOutput(int lid)
{
  checkFunction(_functions->unsetOutput);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->unsetOutput.ptr(_connection, lid);
  if (result < 0)
    throw LiveClientError(result);
}

void LiveClient::synchronizeInput()
{
  checkFunction(_functions->synchronizeInput);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->synchronizeInput.ptr(_connection);
  if (result < 0)
    throw LiveClientError(result);
}

void LiveClient::synchronizeOutput()
{
  checkFunction(_functions->synchronizeOutput);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->synchronizeOutput.ptr(_connection);
  if (result < 0)
    throw LiveClientError(result);
}

bool LiveClient::isUpdateRequired()
{
  checkFunction(_functions->isUpdateRequired);

  if (_connection == 0)
    throw UninitializedClientError();

  return _functions->isUpdateRequired.ptr(_connection);
}

bool LiveClient::staticInfoChanged()
{
  checkFunction(_functions->staticInfoChanged);

  if (_connection == 0)
    throw UninitializedClientError();

  return _functions->staticInfoChanged.ptr(_connection);
}

bool LiveClient::dynamicInfoChanged()
{
  checkFunction(_functions->dynamicInfoChanged);

  if (_connection == 0)
    throw UninitializedClientError();

  return _functions->dynamicInfoChanged.ptr(_connection);
}

char LiveClient::pointQuality(int lid)
{
  checkFunction(_functions->pointQuality);

  if (_connection == 0)
    throw UninitializedClientError();

  char result = _functions->pointQuality.ptr(_connection, lid);
  if (result < 0)
    throw LiveClientError(result);

  return result;
}

int LiveClient::pointSID(int lid)
{
  checkFunction(_functions->pointSID);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->pointSID.ptr(_connection, lid);
  if (result < 0)
    throw LiveClientError(result);

  return result;
}

std::string LiveClient::pointIESS(int lid)
{
  checkFunction(_functions->pointIESS);

  if (_connection == 0)
    throw UninitializedClientError();

  const char* result = _functions->pointIESS.ptr(_connection, lid);
  if (result == 0)
    throw LiveClientError(LiveErrorCode_InvalidResult);

  return result;
}

std::string LiveClient::pointZD(int lid)
{
  checkFunction(_functions->pointZD);

  if (_connection == 0)
    throw UninitializedClientError();

  const char* result = _functions->pointZD.ptr(_connection, lid);
  if (result == 0)
    throw LiveClientError(LiveErrorCode_InvalidResult);

  return result;
}

std::string LiveClient::pointIDCS(int lid)
{
  checkFunction(_functions->pointIDCS);

  if (_connection == 0)
    throw UninitializedClientError();

  const char* result = _functions->pointIDCS.ptr(_connection, lid);
  if (result == 0)
    throw LiveClientError(LiveErrorCode_InvalidResult);

  return result;
}

std::string LiveClient::pointDESC(int lid)
{
  checkFunction(_functions->pointDESC);

  if (_connection == 0)
    throw UninitializedClientError();

  const char* result = _functions->pointDESC.ptr(_connection, lid);
  if (result == 0)
    throw LiveClientError(LiveErrorCode_InvalidResult);

  return result;
}

std::string LiveClient::pointAUX(int lid)
{
  checkFunction(_functions->pointAUX);

  if (_connection == 0)
    throw UninitializedClientError();

  const char* result = _functions->pointAUX.ptr(_connection, lid);
  if (result == 0)
    throw LiveClientError(LiveErrorCode_InvalidResult);

  return result;
}

std::string LiveClient::pointRTString(int lid)
{
  checkFunction(_functions->pointRTString);

  if (_connection == 0)
    throw UninitializedClientError();

  const char* result = _functions->pointRTString.ptr(_connection, lid);
  if (result == 0)
    throw LiveClientError(LiveErrorCode_InvalidResult);

  return result;
}

char LiveClient::pointAR(int lid)
{
  checkFunction(_functions->pointAR);

  if (_connection == 0)
    throw UninitializedClientError();

  char result = _functions->pointAR.ptr(_connection, lid);
  if (result < 0)
    throw LiveClientError(result);

  return result;
}

char LiveClient::pointRT(int lid)
{
  checkFunction(_functions->pointRT);

  if (_connection == 0)
    throw UninitializedClientError();

  char result = _functions->pointRT.ptr(_connection, lid);
  if (result < 0)
    throw LiveClientError(result);

  return result;
}

std::string LiveClient::pointValue(int lid)
{
  checkFunction(_functions->pointValue);

  if (_connection == 0)
    throw UninitializedClientError();

  const char* result = _functions->pointValue.ptr(_connection, lid);
  if (result == 0)
    throw LiveClientError(LiveErrorCode_InvalidResult);

  return result;
}

PointGroups LiveClient::pointSecGroups(int lid)
{
  checkFunction(_functions->pointSecGroups);

  if (_connection == 0)
    throw UninitializedClientError();

  const unsigned char* result =
    _functions->pointSecGroups.ptr(_connection, lid);
  if (result == 0)
    throw LiveClientError(LiveErrorCode_InvalidResult);

  PointGroups groups(256);
  for (int i = 0; i < 256; i++)
    groups[i] = ((result[i / 8] & (0x01 << (i % 8))) != 0);
  return groups;
}

PointGroups LiveClient::pointTechGroups(int lid)
{
  checkFunction(_functions->pointTechGroups);

  if (_connection == 0)
    throw UninitializedClientError();

  const unsigned char* result =
    _functions->pointTechGroups.ptr(_connection, lid);
  if (result == 0)
    throw LiveClientError(LiveErrorCode_InvalidResult);

  PointGroups groups(256);
  for (int i = 0; i < 256; i++)
    groups[i] = ((result[i / 8] & (0x01 << (i % 8))) != 0);
  return groups;
}

float LiveClient::readAnalog(int lid, char* quality)
{
  checkFunction(_functions->readAnalog);

  if (_connection == 0)
    throw UninitializedClientError();

  float value;
  char tmpQuality;
  int result = _functions->readAnalog.ptr(
    _connection, lid, &value, &tmpQuality);
  if (result < 0)
    throw LiveClientError(result);

  if (quality != 0)
    *quality = tmpQuality;

  return value;
}

double LiveClient::readDouble(int lid, char* quality)
{
  checkFunction(_functions->readDouble);

  if (_connection == 0)
    throw UninitializedClientError();

  double value;
  char tmpQuality;
  int result = _functions->readDouble.ptr(
    _connection, lid, &value, &tmpQuality);
  if (result < 0)
    throw LiveClientError(result);

  if (quality != 0)
    *quality = tmpQuality;

  return value;
}

dword LiveClient::readPacked(int lid, char* quality)
{
  checkFunction(_functions->readPacked);

  if (_connection == 0)
    throw UninitializedClientError();

  dword value;
  char tmpQuality;
  int result = _functions->readPacked.ptr(
    _connection, lid, &value, &tmpQuality);
  if (result < 0)
    throw LiveClientError(result);

  if (quality != 0)
    *quality = tmpQuality;

  return value;
}

llong LiveClient::readInt64(int lid, char* quality)
{
  checkFunction(_functions->readInt64);

  if (_connection == 0)
    throw UninitializedClientError();

  llong value;
  char tmpQuality;
  int result = _functions->readInt64.ptr(
    _connection, lid, &value, &tmpQuality);
  if (result < 0)
    throw LiveClientError(result);

  if (quality != 0)
    *quality = tmpQuality;

  return value;
}

bool LiveClient::readBinary(int lid, char* quality)
{
  checkFunction(_functions->readBinary);

  if (_connection == 0)
    throw UninitializedClientError();

  unsigned char value;
  char tmpQuality;
  int result = _functions->readBinary.ptr(
    _connection, lid, &value, &tmpQuality);
  if (result < 0)
    throw LiveClientError(result);

  if (quality != 0)
    *quality = tmpQuality;

  return (value != 0);
}

void LiveClient::write(int lid, float value, Quality quality)
{
  checkFunction(_functions->writeAnalog);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->writeAnalog.ptr(
    _connection, lid, value, static_cast<char>(quality));
  if (result < 0)
    throw LiveClientError(result);
}

void LiveClient::write(int lid, double value, Quality quality)
{
  checkFunction(_functions->writeDouble);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->writeDouble.ptr(
    _connection, lid, value, static_cast<char>(quality));
  if (result < 0)
    throw LiveClientError(result);
}

void LiveClient::write(int lid, dword value, Quality quality)
{
  checkFunction(_functions->writePacked);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->writePacked.ptr(
    _connection, lid, value, static_cast<char>(quality));
  if (result < 0)
    throw LiveClientError(result);
}

void LiveClient::write(int lid, llong value, Quality quality)
{
  checkFunction(_functions->writeInt64);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->writeInt64.ptr(
    _connection, lid, value, static_cast<char>(quality));
  if (result < 0)
    throw LiveClientError(result);
}

void LiveClient::write(int lid, bool value, Quality quality)
{
  checkFunction(_functions->writeBinary);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->writeBinary.ptr(
    _connection, lid, value ? 1 : 0, static_cast<char>(quality));
  if (result < 0)
    throw LiveClientError(result);
}

FieldId LiveClient::fieldIdFromName(const char* name)
{
  checkFunction(_functions->fieldIdFromName);

  int result = _functions->fieldIdFromName.ptr(name);
  if (result < 0)
    throw LiveClientError(result);

  return result;
}

FieldId LiveClient::fieldIdFromWDPFName(const char* name)
{
  checkFunction(_functions->fieldIdFromWDPFName);

  int result = _functions->fieldIdFromWDPFName.ptr(name);
  if (result < 0)
    throw LiveClientError(result);

  return result;
}

int LiveClient::readFieldInt(int lid, FieldId field_id)
{
  checkFunction(_functions->readFieldInt);

  if (_connection == 0)
    throw UninitializedClientError();

  int value;
  int result = _functions->readFieldInt.ptr(
    _connection, lid, field_id, &value);
  if (result < 0)
    throw LiveClientError(result);

  return value;
}

float LiveClient::readFieldFloat(int lid, FieldId field_id)
{
  checkFunction(_functions->readFieldFloat);

  if (_connection == 0)
    throw UninitializedClientError();

  float value;
  int result = _functions->readFieldFloat.ptr(
    _connection, lid, field_id, &value);
  if (result < 0)
    throw LiveClientError(result);

  return value;
}

double LiveClient::readFieldDouble(int lid, FieldId field_id)
{
  checkFunction(_functions->readFieldDouble);

  if (_connection == 0)
    throw UninitializedClientError();

  double value;
  int result = _functions->readFieldDouble.ptr(
    _connection, lid, field_id, &value);
  if (result < 0)
    throw LiveClientError(result);

  return value;
}

std::string LiveClient::readFieldString(int lid, FieldId field_id)
{
  checkFunction(_functions->readFieldString);

  if (_connection == 0)
    throw UninitializedClientError();

  std::vector<char> value(256);
  for (int retries = 0; retries < 8; ++retries)
  {
    int result = _functions->readFieldString.ptr(
      _connection, lid, field_id, &value[0], static_cast<int>(value.size()));
    if (result < 0)
      throw LiveClientError(result);

    // check if buffer size was sufficient
    if (static_cast<size_t>(result) <= value.size())
      return &value[0];
 
    value.resize(result);
  }

  // shouldn't happen (badly written backend or something is
  // constantly increasing field size)
  throw LiveClientError(LiveErrorCode_InvalidResult);
}

int LiveClient::readFieldInt(int lid, const char* field_name)
{
  checkFunction(_functions->readFieldIntByName);

  if (_connection == 0)
    throw UninitializedClientError();

  int value;
  int result = _functions->readFieldIntByName.ptr(
    _connection, lid, field_name, &value);
  if (result < 0)
    throw LiveClientError(result);

  return value;
}

int LiveClient::readWDPFFieldInt(int lid, const char* field_name)
{
  checkFunction(_functions->readFieldIntByWDPFName);

  if (_connection == 0)
    throw UninitializedClientError();

  int value;
  int result = _functions->readFieldIntByWDPFName.ptr(
    _connection, lid, field_name, &value);
  if (result < 0)
    throw LiveClientError(result);

  return value;
}

float LiveClient::readFieldFloat(int lid, const char* field_name)
{
  checkFunction(_functions->readFieldFloatByName);

  if (_connection == 0)
    throw UninitializedClientError();

  float value;
  int result = _functions->readFieldFloatByName.ptr(
    _connection, lid, field_name, &value);
  if (result < 0)
    throw LiveClientError(result);

  return value;
}

float LiveClient::readWDPFFieldFloat(int lid, const char* field_name)
{
  checkFunction(_functions->readFieldFloatByWDPFName);

  if (_connection == 0)
    throw UninitializedClientError();

  float value;
  int result = _functions->readFieldFloatByWDPFName.ptr(
    _connection, lid, field_name, &value);
  if (result < 0)
    throw LiveClientError(result);

  return value;
}

double LiveClient::readFieldDouble(int lid, const char* field_name)
{
  checkFunction(_functions->readFieldDoubleByName);

  if (_connection == 0)
    throw UninitializedClientError();

  double value;
  int result = _functions->readFieldDoubleByName.ptr(
    _connection, lid, field_name, &value);
  if (result < 0)
    throw LiveClientError(result);

  return value;
}

double LiveClient::readWDPFFieldDouble(int lid, const char* field_name)
{
  checkFunction(_functions->readFieldDoubleByWDPFName);

  if (_connection == 0)
    throw UninitializedClientError();

  double value;
  int result = _functions->readFieldDoubleByWDPFName.ptr(
    _connection, lid, field_name, &value);
  if (result < 0)
    throw LiveClientError(result);

  return value;
}

std::string LiveClient::readFieldString(int lid, const char* field_name)
{
  checkFunction(_functions->readFieldStringByName);

  if (_connection == 0)
    throw UninitializedClientError();

  std::vector<char> value(256);
  for (int retries = 0; retries < 8; ++retries)
  {
    int result = _functions->readFieldStringByName.ptr(
      _connection, lid, field_name, &value[0], static_cast<int>(value.size()));
    if (result < 0)
      throw LiveClientError(result);

    // check if buffer size was sufficient
    if (static_cast<size_t>(result) <= value.size())
      return &value[0];
 
    value.resize(result);
  }

  // shouldn't happen (badly written backend or something is
  // constantly increasing field size)
  throw LiveClientError(LiveErrorCode_InvalidResult);
}

std::string LiveClient::readWDPFFieldString(int lid, const char* field_name)
{
  checkFunction(_functions->readFieldStringByWDPFName);

  if (_connection == 0)
    throw UninitializedClientError();

  std::vector<char> value(256);
  for (int retries = 0; retries < 8; ++retries)
  {
    int result = _functions->readFieldStringByWDPFName.ptr(
      _connection, lid, field_name, &value[0], static_cast<int>(value.size()));
    if (result < 0)
      throw LiveClientError(result);

    // check if buffer size was sufficient
    if (static_cast<size_t>(result) <= value.size())
      return &value[0];
 
    value.resize(result);
  }

  // shouldn't happen (badly written backend or something is
  // constantly increasing field size)
  throw LiveClientError(LiveErrorCode_InvalidResult);
}

llong LiveClient::readAT(int lid, bool asMicroSeconds)
{
  checkFunction(_functions->readAT);

  if (_connection == 0)
    throw UninitializedClientError();

  dword seconds = 0;
  dword useconds = 0;

  int result = _functions->readAT.ptr(_connection, lid, &seconds, &useconds);
  if (result < 0)
    throw LiveClientError(result);

  if (asMicroSeconds)
    return convertToMicroSeconds(seconds, useconds);

  return convertToSeconds(seconds, useconds);
}

void LiveClient::writeAT(int lid, dword seconds, dword useconds)
{
  checkFunction(_functions->writeAT);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->writeAT.ptr(_connection, lid, seconds, useconds);
  if (result < 0)
    throw LiveClientError(result);
}

void LiveClient::writeST(int lid, dword value, dword mask)
{
  checkFunction(_functions->writeST);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->writeST.ptr(_connection, lid, value, mask);
  if (result < 0)
    throw LiveClientError(result);
}

void LiveClient::writeXSTn(int lid, int n, int value, int mask)
{
  checkFunction(_functions->writeXSTn);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->writeXSTn.ptr(
    _connection, lid, n, value, mask);
  if (result < 0)
    throw LiveClientError(result);
}

template <typename FunctionPtr>
void LiveClient::initializeFunction(
  Function<FunctionPtr>& function, const std::string& functionName)
{
  std::string exportName;

  if (functionName.size() == 0)
    return;

  function.functionName = functionName;

  // add prefix and capitalize first letter of function name
  function.exportName.reserve(256);
  function.exportName = "EDSLive";
  function.exportName += (char)toupper(functionName[0]);
  for (size_t i = 1; i < functionName.size(); ++i)
    function.exportName += functionName[i];

  function.ptr = reinterpret_cast<FunctionPtr>(_backend->resolveExport(
    function.exportName.c_str()));
}

template <typename FunctionPtr>
void LiveClient::checkFunction(const Function<FunctionPtr>& function) const
{
  if (!function.isSupportedByBackend())
    throwUnsupportedFunction(function);
}

template <typename FunctionPtr>
void LiveClient::throwUnsupportedFunction(const Function<FunctionPtr>& function) const
{
  throw UnsupportedFunctionError(
    function.functionName, function.exportName, _backend->type(), _backend->version());
}


/** LiveClientError **/

LiveClientError::LiveClientError(int errorCode)
  : Error(formatErrorString(errorCode)),
    _errorCode(errorCode)
{
}

std::string LiveClientError::formatErrorString(int errorCode)
{
  std::stringstream ss;
  ss << "Live client error (" << errorCode << ") has occured";
  return ss.str();
}

}

}
