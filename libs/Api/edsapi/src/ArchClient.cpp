// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

#include "../include/ArchClient.h"

#include <memory>
#include <sstream>
#include "Backend.h"

using namespace eds;
using namespace eds::detail;

// types from eds namespace must be visible before
// ArchBackend.h is included
#include "ArchBackend.h"

namespace eds
{

namespace arch
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
  Function<EDSArchGetFunctionPtr> getFunction;
  Function<EDSArchDestroyFunctionPtr> destroyFunction;
  Function<EDSArchPushPointParamPtr> pushPointParam;
  Function<EDSArchPushTimestampParamPtr> pushTimestampParam;
  Function<EDSArchPushValueParamPtr> pushValueParam;
  Function<EDSArchClearParamsPtr> clearParams;
  Function<EDSArchInitPtr> init;
  Function<EDSArchInitializeAsAgentPtr> initializeAsAgent;
  Function<EDSArchInitializeAsUserPtr> initializeAsUser;
  Function<EDSArchShutPtr> shut;
  Function<EDSArchSetupLoggerPtr> setupLogger;
  Function<EDSArchAddQueryPtr> addQuery;
  Function<EDSArchGetResponsePtr> getResponse;
  Function<EDSArchClearAllPtr> clearAll;
  Function<EDSArchExecuteQueriesPtr> executeQueries;
  Function<EDSArchExecuteQueryPtr> executeQuery;
  Function<EDSArchNewConnectionPtr> newConnection;
  Function<EDSArchDestroyConnectionPtr> destroyConnection;
  Function<EDSArchAddTabTrendPtr> addTabTrend;
  Function<EDSArchExecuteTabTrendsPtr> executeTabTrends;
  Function<EDSArchFetchTabTrendRowPtr> fetchTabTrendRow;
  Function<EDSArchDestroyTabTrendRowPtr> destroyTabTrendRow;
  Function<EDSArchPushTabTrendParamPtr> pushTabTrendParam;
  Function<EDSArchCreateTabTrendPtr> createTabTrend;
  Function<EDSArchDestroyTabTrendPtr> destroyTabTrend;
  Function<EDSArchClearTabTrendParamsPtr> clearTabTrendParams;
  Function<EDSArchWriteShadesPtr> writeShades;
  Function<EDSArchAddShadeValuePtr> addShadeValue;
};


/** ArchClient **/

ArchClient::ArchClient(const char* version)
  : _backend(new Backend("arch", version)),
    _connection(0)
{
  std::unique_ptr<FunctionTable> functions = std::make_unique<FunctionTable>();

#define EDSAPI_INITIALIZE_FUNCTION(functionName) \
  initializeFunction(functions->functionName, #functionName);

  EDSAPI_INITIALIZE_FUNCTION(getFunction);
  EDSAPI_INITIALIZE_FUNCTION(destroyFunction);
  EDSAPI_INITIALIZE_FUNCTION(pushPointParam);
  EDSAPI_INITIALIZE_FUNCTION(pushTimestampParam);
  EDSAPI_INITIALIZE_FUNCTION(pushValueParam);
  EDSAPI_INITIALIZE_FUNCTION(clearParams);
  EDSAPI_INITIALIZE_FUNCTION(init);
  EDSAPI_INITIALIZE_FUNCTION(initializeAsAgent);
  EDSAPI_INITIALIZE_FUNCTION(initializeAsUser);
  EDSAPI_INITIALIZE_FUNCTION(shut);
  EDSAPI_INITIALIZE_FUNCTION(setupLogger);
  EDSAPI_INITIALIZE_FUNCTION(addQuery);
  EDSAPI_INITIALIZE_FUNCTION(getResponse);
  EDSAPI_INITIALIZE_FUNCTION(clearAll);
  EDSAPI_INITIALIZE_FUNCTION(executeQueries);
  EDSAPI_INITIALIZE_FUNCTION(executeQuery);
  EDSAPI_INITIALIZE_FUNCTION(newConnection);
  EDSAPI_INITIALIZE_FUNCTION(destroyConnection);
  EDSAPI_INITIALIZE_FUNCTION(addTabTrend);
  EDSAPI_INITIALIZE_FUNCTION(executeTabTrends);
  EDSAPI_INITIALIZE_FUNCTION(fetchTabTrendRow);
  EDSAPI_INITIALIZE_FUNCTION(destroyTabTrendRow);
  EDSAPI_INITIALIZE_FUNCTION(pushTabTrendParam);
  EDSAPI_INITIALIZE_FUNCTION(createTabTrend);
  EDSAPI_INITIALIZE_FUNCTION(destroyTabTrend);
  EDSAPI_INITIALIZE_FUNCTION(clearTabTrendParams);
  EDSAPI_INITIALIZE_FUNCTION(writeShades);
  EDSAPI_INITIALIZE_FUNCTION(addShadeValue);

#undef EDSAPI_INITIALIZE_FUNCTION

  checkFunction(functions->newConnection);

  _connection = functions->newConnection.ptr();
  if (_connection == 0)
    throw ArchClientError(ArchErrorCode_InvalidResult);

  _functions = functions.release();
}

ArchClient::~ArchClient()
{
  if (_connection != 0)
  {
    if (_functions->destroyConnection.ptr != 0)
      _functions->destroyConnection.ptr(_connection);
  }

  delete _functions;
  delete _backend;
}

void ArchClient::setupLogger(const char* str)
{
  checkFunction(_functions->setupLogger);

  _functions->setupLogger.ptr(str);
}

void ArchClient::init(const char* lhost, word lport,
                      const char* rhost, word rport,
                      word lport_range, word max_packet)
{
  checkFunction(_functions->init);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->init.ptr(
    _connection, lhost, lport, rhost, rport,
    lport_range, max_packet);
  if (result < 0)
    throw ArchClientError(result);
}

void ArchClient::initializeAsAgent(const char* program_name,
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
                                                   program_name,
                                                   instance_name,
                                                   lhost,
                                                   lport,
                                                   rhost,
                                                   rport,
                                                   lport_range,
                                                   max_packet);
    if (result < 0)
      throw ArchClientError(result);
    return;
  }

  int result = _functions->init.ptr(
    _connection, lhost, lport, rhost, rport, lport_range, max_packet);
  if (result < 0)
    throw ArchClientError(result);
}

void ArchClient::initializeAsUser(const char* user_name,
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
    throw ArchClientError(result);
}

void ArchClient::shut()
{
  checkFunction(_functions->shut);

  if (_connection == 0)
    throw UninitializedClientError();

  _functions->shut.ptr(_connection);
}

void ArchClient::clear()
{
  checkFunction(_functions->clearAll);

  if (_connection == 0)
    throw UninitializedClientError();

  _functions->clearAll.ptr(_connection);
}

ReportFunction* ArchClient::getReportFunction(const char* name)
{
  checkFunction(_functions->getFunction);

  if (_connection == 0)
    throw UninitializedClientError();

  EDSArchFunctionPtr internalFunction = _functions->getFunction.ptr(name);
  if (internalFunction == 0)
    throw ArchClientError(ArchErrorCode_InvalidResult);

  return new ReportFunction(_backend, _functions, internalFunction);
}

QueryId ArchClient::addQuery(ReportFunction* function)
{
  checkFunction(_functions->addQuery);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->addQuery.ptr(
    _connection, (function != 0) ? function->_internalFunction : 0);
  if (result < 0)
    throw ArchClientError(result);

  return result;
}

double ArchClient::getResponse(QueryId id, char* quality)
{
  checkFunction(_functions->getResponse);

  if (_connection == 0)
    throw UninitializedClientError();

  double value;
  char tmpQuality;
  int result = _functions->getResponse.ptr(
    _connection, id, &value, &tmpQuality);
  if (result < 0)
    throw ArchClientError(result);

  if (quality != 0)
    *quality = tmpQuality;

  return value;
}

void ArchClient::executeQueries()
{
  checkFunction(_functions->executeQueries);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->executeQueries.ptr(_connection);
  if (result < 0)
    throw ArchClientError(result);
}

double ArchClient::executeQuery(ReportFunction* function, char* quality)
{
  checkFunction(_functions->executeQuery);

  if (_connection == 0)
    throw UninitializedClientError();

  double value;
  char tmpQuality;
  int result = _functions->executeQuery.ptr(
    _connection, (function != 0) ? function->_internalFunction : 0,
    &value, &tmpQuality);
  if (result < 0)
    throw ArchClientError(result);

  if (quality != 0)
    *quality = tmpQuality;

  return value;
}

TabularTrend* ArchClient::getTabularTrend(int sid, const char* function)
{
  checkFunction(_functions->createTabTrend);

  if (_connection == 0)
    throw UninitializedClientError();

  EDSArchTabTrendPtr internalTrend =
    _functions->createTabTrend.ptr(sid, function);
  if (internalTrend == 0)
    throw ArchClientError(ArchErrorCode_InvalidResult);

  return new TabularTrend(_backend, _functions, internalTrend);
}

void ArchClient::addTabularTrend(TabularTrend* trend, unsigned char shade_mode)
{
  checkFunction(_functions->addTabTrend);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->addTabTrend.ptr(
    _connection, (trend != 0) ? trend->_internalTabTrend : 0, shade_mode);
  if (result < 0)
    throw ArchClientError(result);
}

void ArchClient::executeTabularTrends(std::time_t ref_time,
                                      long range,
                                      long step)
{
  checkFunction(_functions->executeTabTrends);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->executeTabTrends.ptr(
    _connection, (int)ref_time, range, step);
  if (result < 0)
    throw ArchClientError(result);
}

bool ArchClient::fetchTabularTrendRow(TabularTrendRow* row)
{
  checkFunction(_functions->fetchTabTrendRow);

  if (_connection == 0)
    throw UninitializedClientError();

  EDSArchTrendRow* internalTrendRow =
    _functions->fetchTabTrendRow.ptr(_connection);

  if (row != 0 && internalTrendRow != 0)
  {
    row->clear();
    row->reserve(internalTrendRow->count);

    for (size_t i = 0; i < internalTrendRow->count; ++i)
    {
      PointValue point;

      point.ts = internalTrendRow->points[i].ts;
      point.tss = internalTrendRow->points[i].tss;
      point.value = internalTrendRow->points[i].value;
      point.quality = internalTrendRow->points[i].quality;

      row->push_back(point);
    }
  }

  if (internalTrendRow != 0)
    _functions->destroyTabTrendRow.ptr(internalTrendRow);

  return (internalTrendRow != 0);
}

void ArchClient::addShadeValue(int sid,
                               std::time_t start_ts,
                               std::time_t end_ts,
                               float value,
                               char quality)
{
  checkFunction(_functions->addShadeValue);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->addShadeValue.ptr(
    _connection, sid, (int)start_ts, (int)end_ts, value, quality);
  if (result < 0)
    throw ArchClientError(result);
}

void ArchClient::writeShades()
{
  checkFunction(_functions->writeShades);

  if (_connection == 0)
    throw UninitializedClientError();

  int result = _functions->writeShades.ptr(_connection);
  if (result < 0)
    throw ArchClientError(result);
}

template <typename FunctionPtr>
void ArchClient::initializeFunction(
  Function<FunctionPtr>& function, const std::string& functionName)
{
  std::string exportName;

  if (functionName.size() == 0)
    return;

  function.functionName = functionName;

  // add prefix and capitalize first letter of function name
  function.exportName.reserve(256);
  function.exportName = "EDSArch";
  function.exportName += (char)toupper(functionName[0]);
  for (size_t i = 1; i < functionName.size(); ++i)
    function.exportName += functionName[i];

  function.ptr = (FunctionPtr)_backend->resolveExport(
    function.exportName.c_str());
}

template <typename FunctionPtr>
void ArchClient::checkFunction(const Function<FunctionPtr>& function) const
{
  if (function.ptr != 0)
    return;

  throw UnsupportedFunctionError(
    function.functionName, function.exportName,
    _backend->type(), _backend->version());
}

template <typename FunctionPtr>
void ArchClient::throwUnsupportedFunction(const Function<FunctionPtr>& function) const
{
  throw UnsupportedFunctionError(
    function.functionName, function.exportName, _backend->type(), _backend->version());
}


/** ReportFunction **/

ReportFunction::ReportFunction(eds::detail::Backend* backend,
                               FunctionTable* functions,
                               EDSArchFunction* archFunction)
  : _backend(backend),
    _functions(functions),
    _internalFunction(archFunction)
{
}

ReportFunction::~ReportFunction()
{
  if (_internalFunction != 0)
  {
    if (_functions->destroyFunction.ptr != 0)
      _functions->destroyFunction.ptr(_internalFunction);
  }
}

void ReportFunction::pushPointParam(int sid,
                                    unsigned char bits_filter,
                                    unsigned char shade_mode)
{
  checkFunction(_functions->pushPointParam);

  _functions->pushPointParam.ptr(
    _internalFunction, sid, bits_filter, shade_mode);
}

void ReportFunction::pushTimestampParam(std::time_t ts)
{
  checkFunction(_functions->pushTimestampParam);

  _functions->pushTimestampParam.ptr(_internalFunction, (int)ts);
}

void ReportFunction::pushValueParam(double v)
{
  checkFunction(_functions->pushValueParam);

  _functions->pushValueParam.ptr(_internalFunction, v);
}

void ReportFunction::clearParams()
{
  checkFunction(_functions->clearParams);

  _functions->clearParams.ptr(_internalFunction);
}

template <typename FunctionPtr>
void ReportFunction::checkFunction(const Function<FunctionPtr>& function) const
{
  if (function.ptr != 0)
    return;

  throw UnsupportedFunctionError(
    function.functionName, function.exportName,
    _backend->type(), _backend->version());
}


/** TabularTrend **/

TabularTrend::TabularTrend(eds::detail::Backend* backend,
                           FunctionTable* functions,
                           EDSArchTabTrend* archTabTrend)
  : _backend(backend),
    _functions(functions),
    _internalTabTrend(archTabTrend)
{
}

TabularTrend::~TabularTrend()
{
  if (_internalTabTrend != 0)
  {
    if (_functions->destroyTabTrend.ptr != 0)
      _functions->destroyTabTrend.ptr(_internalTabTrend);
  }
}

void TabularTrend::pushParam(double v)
{
  checkFunction(_functions->pushTabTrendParam);

  _functions->pushTabTrendParam.ptr(_internalTabTrend, v);
}

void TabularTrend::clearParams()
{
  checkFunction(_functions->clearTabTrendParams);

  _functions->clearTabTrendParams.ptr(_internalTabTrend);
}

template <typename FunctionPtr>
void TabularTrend::checkFunction(const Function<FunctionPtr>& function) const
{
  if (function.ptr != 0)
    return;

  throw UnsupportedFunctionError(
    function.functionName, function.exportName,
    _backend->type(), _backend->version());
}


/** ArchClientError **/

ArchClientError::ArchClientError(int errorCode)
  : Error(formatErrorString(errorCode)),
    _errorCode(errorCode)
{
}

std::string ArchClientError::formatErrorString(int errorCode)
{
  std::stringstream ss;
  ss << "Arch client error (" << errorCode << ") has occured";
  return ss.str();
}

}

}
