// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

#ifndef EDSAPI_ARCH_BACKEND_H
#define EDSAPI_ARCH_BACKEND_H

#include <time.h>

#define EDSAPI_ARCH_SUCCESS               0
#define EDSAPI_ARCH_BAD_CONNECTION_OBJECT -200
#define EDSAPI_ARCH_NO_SUCH_FUNCTION      -201
#define EDSAPI_ARCH_SHADE_WRITE_FAILED    -202
#define EDSAPI_ARCH_NO_CONNECTION         -203
#define EDSAPI_ARCH_BAD_PARAMS            -204
#define EDSAPI_ARCH_PROTOCOL_MISMATCH     -205
#define EDSAPI_ARCH_REQUEST_ERROR         -206
#define EDSAPI_ARCH_ACCESS_DENIED         -207


extern "C"
{

/** Structure representing EDSArch function.
    Parameters are cleared after every execution. */
struct EDSArchFunction;
typedef EDSArchFunction* EDSArchFunctionPtr;

/** Creates a function using function's name. */
typedef EDSArchFunctionPtr (*EDSArchGetFunctionPtr)(const char* name);

/** Destroys function structure. */
typedef void (*EDSArchDestroyFunctionPtr)(EDSArchFunctionPtr func);

/** Pushes point type param into function's params stack. */
typedef void (*EDSArchPushPointParamPtr)(EDSArchFunctionPtr func,
                                         int sid,
                                         unsigned char packet_point_mask,
                                         unsigned char shade_options);

/** Pushes timestamp type param into function's params stack. */
typedef void (*EDSArchPushTimestampParamPtr)(EDSArchFunctionPtr func,
                                             int ts);

/** Pushes value type param into function's params stack. */
typedef void (*EDSArchPushValueParamPtr)(EDSArchFunctionPtr func,
                                         double v);

/** Clears function's params stack. */
typedef void (*EDSArchClearParamsPtr)(EDSArchFunctionPtr func);

/** Structure that represents connewction to EDS Arch Server*/
struct EDSArchConnection;
typedef EDSArchConnection* EDSArchConnectionPtr;

/** Initializes connection structure using parameters:
    local host, local port,
    remote host, remote port, max packet size */
typedef int (*EDSArchInitPtr)(EDSArchConnectionPtr conn,
                              const char* lhost, word lport,
                              const char* rhost, word rport,
                              word lport_range,
                              word max_packet);

/** Initializes API in agent mode (authentication will be performed using key pair). */
typedef int (*EDSArchInitializeAsAgentPtr)(EDSArchConnectionPtr conn,
                                           const char* program_name,
                                           const char* instance_name,
                                           const char* lhost,
                                           word lport,
                                           const char* rhost,
                                           word rport,
                                           word lport_range,
                                           word max_packet);

/** Initializes API in user mode (authentication will be performed with user name and password). */
typedef int (*EDSArchInitializeAsUserPtr)(EDSArchConnectionPtr conn,
                                          const char* user_name,
                                          const char* password,
                                          const char* lhost,
                                          word lport,
                                          const char* rhost,
                                          word rport,
                                          word lport_range,
                                          word max_packet);

/** Shuts connection to EDS Server. */
typedef void (*EDSArchShutPtr)(EDSArchConnectionPtr conn);

/** Setups logger using setup string.
    For example: str="debug=7 logger=console:7 subsystems=ALL" */
typedef void (*EDSArchSetupLoggerPtr)(const char* str);

/** Addds report query to queries queue. Clears function params -
    function can be used again. Returns query position in queue. */
typedef int (*EDSArchAddQueryPtr)(EDSArchConnectionPtr conn,
                                  EDSArchFunctionPtr func);

/** Reads query response using query position in queue as query id. */
typedef int (*EDSArchGetResponsePtr)(EDSArchConnectionPtr conn,
                                     int id,
                                     double* value,
                                     char* qual);

/** Clears every requests queue. */
typedef void (*EDSArchClearAllPtr)(EDSArchConnectionPtr conn);

/** Executes all queries in queue and sets responses. */
typedef int (*EDSArchExecuteQueriesPtr)(EDSArchConnectionPtr conn);

/** Executes single query and immadiately sets response. Clears all
    queries in queue. */
typedef int (*EDSArchExecuteQueryPtr)(EDSArchConnectionPtr conn,
                                      EDSArchFunctionPtr func,
                                      double* val, char* qual);

/** Creates new connection structure - must be destroyed using
    EDSArchDestroyConnection. */
typedef EDSArchConnectionPtr (*EDSArchNewConnectionPtr)();

/** Destroys connection structure. */
typedef void (*EDSArchDestroyConnectionPtr)(EDSArchConnectionPtr conn);

/** Structure representing archival data tabular trend. */
struct EDSArchTabTrend;
typedef EDSArchTabTrend* EDSArchTabTrendPtr;

/** Structure containing point data. */
struct EDSArchPoint
{
  int ts;
  int tss;
  double value;
  char quality;
};

/** Structure containing one tabular trend row. */
struct EDSArchTrendRow
{
  EDSArchPoint* points;
  unsigned int count;
};

/** Adds tabular trend to trends set. Returns trend position.*/
typedef int (*EDSArchAddTabTrendPtr)(EDSArchConnectionPtr conn,
                                     EDSArchTabTrendPtr trend,
                                     unsigned char shade_mode);

/** Executes all trends from sets. Makes trends rows available for read. */
typedef int (*EDSArchExecuteTabTrendsPtr)(EDSArchConnectionPtr conn,
                                          int ref_time,
                                          int range,
                                          int step);

/** Gets next trend row. This row must be destroyed using 
    EDSArchDestroyTrendRow. */
typedef EDSArchTrendRow* (*EDSArchFetchTabTrendRowPtr)(EDSArchConnectionPtr conn);

/** Destroys trend row structure. */
typedef void (*EDSArchDestroyTabTrendRowPtr)(EDSArchTrendRow* row);

/** Push param to tabular trend params stack. */
typedef void (*EDSArchPushTabTrendParamPtr)(EDSArchTabTrendPtr trend,
                                            double param);

/** Creates tabular trend structure using point sid and function
    name. Returned structure should be destroyed using
    EDSArchDestroyTrend. */
typedef EDSArchTabTrendPtr (*EDSArchCreateTabTrendPtr)(int sid,
                                                       const char* function);
/** Destroys tabular trend structure. */
typedef void (*EDSArchDestroyTabTrendPtr)(EDSArchTabTrendPtr trend);

/** Clears tabular trend's params stack. */
typedef void (*EDSArchClearTabTrendParamsPtr)(EDSArchTabTrendPtr trend);

/** Writes stored shades values to archive server. Returns 0 on success. */
typedef int (*EDSArchWriteShadesPtr)(EDSArchConnectionPtr conn);

/** Adds shade value that will be sent to server by EDSArchWriteShades. */
typedef int (*EDSArchAddShadeValuePtr)(EDSArchConnectionPtr conn,
                                       int sid,
                                       int start_ts,
                                       int end_ts,
                                       float val,
                                       char qual);

} // extern "C"

#endif
