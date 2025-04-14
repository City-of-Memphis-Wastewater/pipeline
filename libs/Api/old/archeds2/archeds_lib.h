// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

/*
 * file:	archeds_lib.h
 * project:	ESSII
 * module:	API
 */

#ifndef _ARCHEDS_LIB_H_
#define _ARCHEDS_LIB_H_

#if defined(__CPPLUS) || defined(__CPLUSPLUS) || defined(__cplusplus)
extern "C"
{
#endif

#if defined(_WIN32) || defined(__WIN32__) || defined(ESS_WIN32)
#define ExternalDecl __declspec(dllexport)
#else
#define ExternalDecl
#endif

#define ARCH_EDS_SUCCESS               0
#define ARCH_EDS_BAD_CONNECTION_OBJECT -200
#define ARCH_EDS_NO_SUCH_FUNCTION      -201
#define ARCH_EDS_SHADE_WRITE_FAILED    -202
#define ARCH_EDS_NO_CONNECTION         -203
#define ARCH_EDS_BAD_PARAMS            -204

  /**
     Defines how should be shade and archival values treated.
  */
  typedef enum
  {
    edsPrefereArch = 0x00,
    edsPrefereShade = 0x01,
    edsArchOnly = 0x02,
    edsShadeOnly = 0x03,
    edsDefault = 0x04
  } ArchEDSShadeMode;

  /** Structure representing ArchEDS function.
      Parameters are cleared after every execution. */
  struct s_ArchEDSFunction;
  typedef struct s_ArchEDSFunction * p_ArchEDSFunction;

  /** Creates a function using function's name. */
  typedef p_ArchEDSFunction (*ArchEDSGetFunction)(const char * name);
  /** Destroys function structure */
  typedef void (*ArchEDSDestroyFunction)(p_ArchEDSFunction func);
  /** Pushes point type param into function's params stack */
  typedef void (*ArchEDSPushPointParam)(p_ArchEDSFunction func,
                                        unsigned long sid,
                                        unsigned char packet_point_mask,
                                        ArchEDSShadeMode shade_options);
  /** Pushes timestamp type param into function's params stack */
  typedef void (*ArchEDSPushTimestampParam)(p_ArchEDSFunction func, long ts);
  /** Pushes value type param into function's params stack */
  typedef void (*ArchEDSPushValueParam)(p_ArchEDSFunction func, double v);
  /** Clears function's params stack */
  typedef void (*ArchEDSClearParams)(p_ArchEDSFunction func);

  /** Structure that represents connewction to EDS Arch Server*/
  struct s_ArchEDSConnection;
  typedef struct s_ArchEDSConnection * p_ArchEDSConnection;

  /** Initializes connection structure using parameters:
      local host, local port,
      remote host, remote port, max packet size */
  typedef int (*ArchEDSInit)(p_ArchEDSConnection conn,
                             const char * lhost, int lport,
                             const char * rhost, int rport,
                             int lport_range, int max_packet);
  /** Shuts connection to EDS Server */
  typedef void (*ArchEDSShut)(p_ArchEDSConnection conn);
  /** Setups logger using setup string.
      For example: str="debug=7 logger=console:7 subsystems=ALL"*/
  typedef void (*ArchEDSSetupLogger)(const char * str);
  /** Addds report query to queries queue. Clears function params -
      function can be used again. Returns query position in queue.*/
  typedef int (*ArchEDSAddQuery)(p_ArchEDSConnection conn,
                                 p_ArchEDSFunction func);
  /** Reads query response using query position in queue as query id*/
  typedef int (*ArchEDSGetResponse)(p_ArchEDSConnection conn,
                                    int id, double* value, char * qual);
  /** Clears every requests queue*/
  typedef void (*ArchEDSClearAll)(p_ArchEDSConnection conn);
  /** Executes all queries in queue and sets resposnes.*/
  typedef int (*ArchEDSExecuteQueries)(p_ArchEDSConnection conn);
  /** Executes single query and immadiately sets response. Clears all
      queries in queue*/
  typedef int (*ArchEDSExecuteQuery)(p_ArchEDSConnection conn,
                                     p_ArchEDSFunction func,
                                     double * val, char * qual);
  /** Creates new connection structure - must be destroyed using
      destroyConnection*/
  typedef p_ArchEDSConnection (*ArchEDSNewConnection)();
  /** Destroys connection structure*/
  typedef void (*ArchEDSDestroyConnection)(p_ArchEDSConnection conn);

  /** Structure representing archival data tabular trend*/
  struct s_ArchEDSTabTrend;
  typedef struct s_ArchEDSTabTrend * p_ArchEDSTabTrend;

  /** Structure containig point data*/
  typedef struct
  {
    long ts;
    long tss;
    double val;
    char qual;
  } ArchEDSPoint;

  /** Structure containing one tabular trend row */
  typedef struct
  {
    ArchEDSPoint * points;
    unsigned int count;
  } ArchEDSTrendRow;

  /** Adds tabular trend to trends set. returns trend position.*/
  typedef int (*ArchEDSAddTabTrend)(p_ArchEDSConnection conn,
                                    p_ArchEDSTabTrend trend,
                                    ArchEDSShadeMode shade_mode);
  /** Executes all trends from sets. Makes trends rows available for read. */
  typedef int (*ArchEDSExecuteTabTrends)(p_ArchEDSConnection conn,
                                         long ref_time,
                                         long range,
                                         long step,
                                         bool useDST);
  /** Gets next trend row. This row must be distroyed using destroyRow*/
  typedef ArchEDSTrendRow* (*ArchEDSFetchTabTrendRow)(p_ArchEDSConnection conn);
  /** Destroys trend row structure*/
  typedef void (*ArchEDSDestroyTrendRow)(ArchEDSTrendRow * row);
  /** Push param to tabular trend params stack*/
  typedef void (*ArchEDSPushTrendParam)(p_ArchEDSTabTrend trend, double param);
  /** Creates tabular trend structure using point sid and funcion
      name. returned structure should be destroyed using
      destroyTrend*/
  typedef p_ArchEDSTabTrend (*ArchEDSCreateTabTrend)(long sid,
                                                     const char * function);
  /** Destroys tabular trend structure */
  typedef void (*ArchEDSDestroyTrend)(p_ArchEDSTabTrend trend);
  /** Clears tabular trend's params stack*/
  typedef void (*ArchEDSClearTrendParams)(p_ArchEDSTabTrend trend);

  /** Writes stored shades values to archive server. Returns 0 on success. */
  typedef int (*ArchEDSWriteShades)(p_ArchEDSConnection conn);
  /** Adds shade value taht will be send to server by writeShades*/
  typedef int (*ArchEDSAddShadeValue)(p_ArchEDSConnection conn,
                                      long sid,
                                      long start_ts,
                                      long end_ts,
                                      float val,
                                      char qual);

  /** Structure containing all library functions. If returned by
      getArchEDSLib it contains proper pointers. All funcions can be
      accesed in library using same names as this structure fields*/
  typedef struct
  {
    ArchEDSGetFunction getFunction;
    ArchEDSDestroyFunction destroyFunction;
    ArchEDSPushPointParam pushPointParam;
    ArchEDSPushTimestampParam pushTimestampParam;
    ArchEDSPushValueParam pushValueParam;
    ArchEDSClearParams clearParams;
    ArchEDSInit init;
    ArchEDSShut shut;
    ArchEDSSetupLogger setupLogger;
    ArchEDSAddQuery addQuery;
    ArchEDSGetResponse getResponse;
    ArchEDSClearAll clearAll;
    ArchEDSExecuteQueries executeQueries;
    ArchEDSExecuteQuery executeQuery;
    ArchEDSNewConnection newConnection;
    ArchEDSDestroyConnection destroyConnection;
    ArchEDSAddTabTrend addTabTrend;
    ArchEDSExecuteTabTrends executeTabTrends;
    ArchEDSFetchTabTrendRow fetchTabTrendRow;
    ArchEDSDestroyTrendRow destroyTrendRow;
    ArchEDSPushTrendParam pushTrendParam;
    ArchEDSCreateTabTrend createTabTrend;
    ArchEDSDestroyTrend destroyTrend;
    ArchEDSClearTrendParams clearTrendParams;
    ArchEDSWriteShades writeShades;
    ArchEDSAddShadeValue addShadeValue;
  } ArchEDSLib;

/* This version should be manually updated after changes in library iface */
#define ARCH_EDS_LIB_VERSION    "9.1 ARCH_API=1"

  /** Returns fully initialized ArchEDSLib static pointer (it
      shouldn't be destroyed)*/
  typedef ArchEDSLib* (*GetArchEDSLib)(const char * version);

#if defined(__CPPLUS) || defined(__CPLUSPLUS) || defined(__cplusplus)
} // extern "C"
#endif

#endif //_ARCHEDS_LIB_H_
