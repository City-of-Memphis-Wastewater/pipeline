// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

#ifndef _LIVEEDS_H_
#define _LIVEEDS_H_

#include <string>
#include "liveeds_lib.h"

#if defined(_WIN32) || defined(__WIN32__)
#ifndef WIN32
#define WIN32
#endif
#include <windows.h>
#endif

#define LIVE_EDS_LIB_ERR -1000

class LiveEDS
{
 public:
  /** Returns library search path. */
  static const char* libraryPath();

  /** Sets library search path.
      Do not include liveeds2 library file in the path
      (only the directory part).
      This method must be called before LiveEDS object is constructed. */
  static void setLibraryPath(const char* path);


  /** Creates wrapper, loads library */
  LiveEDS();

  /** Frees library resources */
  ~LiveEDS();

  /** Setups logger using setup string.
      For example: str="debug=7 logger=console:7 subsystems=ALL"*/
  void setupLogger(const char * str);

  /** Initializes connection structure using parameters:
      local host, local port,
      remote host, remote port, max packet size.
      Mode describes which functions should be available for use. */
  int init(LiveEDSMode mode,
           const char * lhost, int lport,
           const char * rhost, int rport,
           int lport_range,
           int max_packet);
  /** Initializes authenticated client connection structure using parameters:
      user, password,
      local host, local port,
      remote host, remote port, max packet size.
      Mode describes which functions should be available for use. */
  int authInit(const char * user, const char * password,
               const char * lhost, int lport,
               const char * rhost, int rport,
               int lport_range,
               int max_packet);

  /** Shuts connection to EDS Server */
  int shut();

  /** The param iess is similar to WDPF point name. (iess is an abbreviation
      for Identifier of Enterprise Server Signal ) return -1 for not
      existing point , < -1 for error and >=0 for good point */
  long findByIESS(const char * iess);

  /** Similar to findByIESS but performs two searches.
      First is exactly the same as in findByIESS (case sensitive).
      If this search has no results, second search is performed
      (case insensitive). */
  long findByIESS_NoCase( const char * iess);

  /** Usually iess (the name of EDS point similar to WDPF point name)
      is used to get point's lid. In some cases it may be better
      to use idcs and zd name of EDS point, which is provided by this
      function. Idcs is an abbreviation for Identifer of Digital
      Control System.
      Returns -1 for not existing point, < -1 for error, and >=0
      for good point.*/
  long findByIDCS(const char * idcs, const char * zd = 0);

  /** Similiar to findByIDCS but performs two searches.
      First is exactly the same as in findByIDCS (case sensitive).
      If this search has no results, second search is performed
      (case insensitive). */
  long findByIDCS_NoCase(const char * idcs, const char * zd = 0);

  /** Returns point's SID - used for accesing archival data*/
  long getSID(long lid);

  /** Must use this function before any read() from point of given lid.
      Cannot write points which are marked as Input(to read) by this function.
      It is possible to call this function more than once for one lid.
      Returns 0 for ok, !=0 for error.*/
  int setInput(long lid);

  /** Must USE this function before any write() FROM POINT of this lid. Cannot
      read points which are marked as Output(to write) by this
      function. It is not allowed to call this function more than once
      for one lid. Returns 0 for ok, !=0 for error. */
  int setOutput(long lid);

  /** Point will be no longer refreshed during synchronizeInput.
      Returns 0 for ok, !=0 for error. */
  int unsetInput(long lid);

  /** Point will be no longer writen during synchronizeOutput.
      Returns 0 for ok, !=0 for error. */
  int unsetOutput(long lid);


  /** Must be called before any input operation (read, findBy*) and
      after setInput- reads points value from server. Returns 0 for ok,
      !=0 for error.*/
  int synchronizeInput();

  /** Must by called after all write*() calls and before next synchronizeInput.
      return 0 for ok, !=0 for error. */
  int synchronizeOutput();



  /** Reads analog value. Before call this funcion point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      Return 0 for ok, !=0 for error. */
  int read(long lid, float * val, char * qual);

  /** Reads double value. Before call this funcion point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      Return 0 for ok, !=0 for error. */
  int read(long lid, double * val, char * qual);

  /** Reads packet point value. Before call this funcion point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      Return 0 for ok, !=0 for error. */
  int read(long lid, unsigned long * val, char * qual);

  /** Reads int64 point value. Before call this funcion point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      Return 0 for ok, !=0 for error. */
  int read(long lid, int64_t * val, char * qual);

  /** Reads binary point value.  Before call this funcion point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      Return 0 for ok, !=0 for error. */
  int read(long lid, unsigned char * val, char * qual);




  /** Returns field id for given field name, or 0 if no such field exists.
      Works only with EDS standard fields.*/
  int fieldIdFromName(const char* name);
  int fieldIdFromWDPFName(const char* name);

  /** Reads integer field value. For dynamic fields point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      Return 0 for ok, !=0 for error. */
  int readField(long lid, int field_id, int * val);

  /** Reads analog field value. For dynamic fields point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      Return 0 for ok, !=0 for error. */
  int readField(long lid, int field_id, float * val);

  /** Reads double field value. For dynamic fields point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      Return 0 for ok, !=0 for error. */
  int readField(long lid, int field_id, double * val);

  /** Reads string field value and stores it in buffer.
      For dynamic fields point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      Return 0 for ok, !=0 for error. */
  int readField(long lid, int field_id, char * buffer, int buffer_size);

  /** Reads integer field value. For dynamic fields point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      Return 0 for ok, !=0 for error. */
  int readField(long lid, const char * field_name, int * val);
  int readWDPFField(long lid, const char * field_name, int * val);

  /** Reads double field value. For dynamic fields point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      Return 0 for ok, !=0 for error. */
  int readField(long lid, const char * field_name, float * val);
  int readWDPFField(long lid, const char * field_name, float * val);

  /** Reads double field value. For dynamic fields point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      Return 0 for ok, !=0 for error. */
  int readField(long lid, const char * field_name, double * val);
  int readWDPFField(long lid, const char * field_name, double * val);

  /** Reads string field value. For dynamic fields point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      Return 0 for ok, !=0 for error. */
  int readField(long lid, const char * field_name,
                char * buffer,
                int buffer_size);
  int readWDPFField(long lid, const char * field_name,
                char * buffer,
                int buffer_size);

  /** Writes analog value. Before call to this funcion point must be
      already inited by setOutput. Return 0 for ok, !=0 for error. */
  int write(long lid, float * val, char * qual);

  /** Writes double value. Before call to this funcion point must be
      already inited by setOutput. Return 0 for ok, !=0 for error. */
  int write(long lid, double * val, char * qual);

  /** Writes packet value. Before call to this funcion point must be
      already inited by setOutput. Return 0 for ok, !=0 for error. */
  int write(long lid, unsigned long * val, char * qual);

  /** Writes int64 value. Before call to this funcion point must be
      already inited by setOutput. Return 0 for ok, !=0 for error. */
  int write(long lid, int64_t * val, char * qual);

  /** Writes binary value. Before call to this funcion point must be
      already inited by setOutput. Return 0 for ok, !=0 for error. */
  int write(long lid, unsigned char * val, char * qual);

  /** Writes point's ST field value.
      Point must be set for output.
      Return 0 for ok, != for error. Stored in library as: writeStatus */
  int writeStatus(long lid, unsigned int value, unsigned int mask=0xFFFFFFFF);

  /** Writes point's XSTn field value, where n can be on of {1,2,3}.
      Point must be set for output.
      Return 0 for ok, != for error. Stored in library as: writeXSTn */
  int writeXSTn(long lid, int n, int value, int mask=0xFFFFFFFF);

 private:
  static std::string lib_path;

  LiveEDSLib * lib;
  p_LiveEDSConnection conn;
#ifdef WIN32
  HANDLE lib_handle;
#else
  void * lib_handle;
#endif
};

#endif //_LIVEEDS_H_
