// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

/*
 * file:	archeds.h
 * project:	ESSII
 * module:	API
 */

#ifndef _ARCHEDS_H_
#define _ARCHEDS_H_

#include "archeds_lib.h"

#if defined(_WIN32) || defined(__WIN32__)
# if !defined(WIN32)
#  define WIN32
# endif
# include <windows.h>
#endif

#include <memory>

#define ARCH_EDS_LIB_ERR -1000

#include <string>

class EDSFunction
{
 public:
  /** For wrapper internal use only */
  EDSFunction(ArchEDSLib * lib, const char * name);
  /** For wrapper internal use only */
  virtual ~EDSFunction();

  /** Pushes point type param into function's params stack */
  void pushPointParam(unsigned long sid,
                      unsigned char packet_point_mask = 0xFF,
                      ArchEDSShadeMode = edsDefault);
  /** Pushes timestamp type param into function's params stack */
  void pushTimestampParam(long ts);
  /** Pushes value type param into function's params stack */
  void pushValueParam(double v);
  /** Clears function's params stack */
  void clearParams();

  /** For wrapper internal use only */
  p_ArchEDSFunction getDefinition() { return func; }
 private:
  EDSFunction(const EDSFunction&);
  p_ArchEDSFunction func;
  ArchEDSLib * lib;

};
typedef std::shared_ptr<EDSFunction> EDSFunction_ptr;


class EDSTabTrend
{
 public:
  /** For wrapper internal use only */
  EDSTabTrend(ArchEDSLib * lib, long sid, const char * func);
  /** For wrapper internal use only */
  virtual ~EDSTabTrend();

  /** Clears tabular trend's params stack*/
  void clearParams();
  /** Push param to tabular trend params stack*/
  void pushParam(double v);

  /** For wrapper internal use only */
  p_ArchEDSTabTrend getDefinition() { return trend; }

 private:
  EDSTabTrend(const EDSTabTrend&);
  p_ArchEDSTabTrend trend;
  ArchEDSLib * lib;
};
typedef std::shared_ptr<EDSTabTrend> EDSTabTrend_ptr;

class ArchEDS
{
 public:
  static void setLibrarySearchPath(const char *searchPath);

  /** Default wrapper constructor - creates wrapper and loads library */
  ArchEDS();
  /** Frees library */
  virtual ~ArchEDS();

  /** Initializes connection structure using parameters:
      local host, local port,
      remote host, remote port, max packet size.
      Mode describes what functions should be available. */
  int init(const char * lhost, int lport,
           const char * rhost, int rport,
           int lport_range, int max_packet);
  /** Shuts connection to EDS Archive Server */
  void shut();
  /** Setups logger using setup string.
      For example: str="debug=7 logger=console:7 subsystems=ALL"*/
  void setupLogger(const char *);

  /** Creates a function using function's name*/
  EDSFunction_ptr getFunction(const char * name);

  /** Adds report query to queries queue. Clears function params -
      function can be used again. Returns query position in queue.*/
  int addQuery(EDSFunction_ptr& function);
  /** Reads query response using query position in queue as query id*/
  int getResponse(int id, double* value, char* qual);
  /** Clears all queries (including tabular and shade write) queue*/
  void clear();
  /** Executes all queries in queue and sets responses*/
  int executeQueries();

  /** Executes single query and immediately sets response. Clears all
      queries in queue*/
  int executeQuery(EDSFunction_ptr& function, double* value, char* qual);

  /** Creates tabular trend structure using point sid and funcion
      name. */
  EDSTabTrend_ptr getTabTrend(long sid, const char * func)
    { return EDSTabTrend_ptr(new EDSTabTrend(lib,sid,func)); }

  /** Adds tabular trend to trends set. Returns trend position.*/
  int addTabTrend(EDSTabTrend_ptr& trend,
                  ArchEDSShadeMode shade_mode = edsDefault );
  /** Executes all trends from trends set.
      Makes trends rows available for read. */
  int executeTabTrends(long ref_time, long range, long step, bool useDST = true);
  /** Gets next trend row. This row must be destroyed using destroyTrendRow*/
  ArchEDSTrendRow * fetchTabTrendRow();
  /** Properly destroys ArchEDSTrendRow given by fetchTabTrendRow*/
  void destroyTrendRow(ArchEDSTrendRow * row);

  /** Writes stored shades values to archive server. Returns 0 on success. */
  int writeShades();

  /** Adds shade value that will be sent to server by writeShades*/
  int addShadeValue(long sid,
                    long start_ts,
                    long end_ts,
                    float val,
                    char qual);

 private:
  static std::string lib_search_path;

  ArchEDS(const ArchEDS&){}
  ArchEDSLib * lib;
  p_ArchEDSConnection conn;
#ifdef WIN32
  HANDLE lib_handle;
#else
  void * lib_handle;
#endif

};

#endif //_ARCHEDS_H_
