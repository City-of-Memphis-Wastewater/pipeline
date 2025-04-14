// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

#ifndef __LIVEEDS_LIB_H_
#define __LIVEEDS_LIB_H_

#include <sys/types.h>

#if defined(__CPPLUS) || defined(__CPLUSPLUS) || defined(__cplusplus)
extern "C"
{
#endif

#if defined(_WIN32) || defined(__WIN32__) || defined(ESS_WIN32)
# define ExternalDecl __declspec(dllexport)
  typedef __int64 int64_t;
#else
# define ExternalDecl
  // gcc should have int64_t defined
#endif

#define EDS_LIB_NO_ERROR                  0
#define EDS_LIB_ERR_BAD_CONNECTION_OBJECT -100
#define EDS_LIB_ERR_UNINITIALIZED_SOCKET  -101
#define EDS_LIB_ERR_UNINITIALIZED_AGENT   -102
#define EDS_LIB_ERR_PROTOCOL_MISMATCH     -103
#define EDS_LIB_ERR_ACCESS_DENIED         -104
#define EDS_LIB_ERR_NOT_LOGGED_IN         -105
#define EDS_LIB_ERR_NOT_SYNCHRONIZED      -106
#define EDS_LIB_ERR_RESPONSE_TIMEOUT      -107
#define EDS_LIB_ERR_BIDIRECTIONAL_POINT   -108

  typedef unsigned char byte;

  /** Defines access modes - determines count and kinds of opened
      sockets*/
  typedef enum
  {
    edsRead = 0x01,
    edsWrite = 0x10,
    edsReadWrite = 0x11
  } LiveEDSMode;

  /** structure that represents connection to EDS Server*/
  struct s_LiveEDSConnection;
  typedef struct s_LiveEDSConnection * p_LiveEDSConnection;

  /** Initializes connection structure using parameters:
      local host, local port,
      remote host, remote port, max packet size */
  typedef int (*LiveEDSInit)(p_LiveEDSConnection connection,
                             LiveEDSMode mode,
                             const char * lhost, int lport,
                             const char * rhost, int rport,
                             int lport_range,
                             int max_packet);

  /** Initializes authenticated client connection structure using parameters:
      user, password,
      local host, local port,
      remote host, remote port, max packet size */
  typedef int (*LiveEDSAuthInit)(p_LiveEDSConnection connection,
                                 const char * user, const char * password,
                                 const char * lhost, int lport,
                                 const char * rhost, int rport,
                                 int lport_range,
                                 int max_packet);

  /** Setups logger using setup string.
      For example: str="debug=7 logger=console:7 subsystems=ALL"*/
  typedef void (*LiveEDSSetupLogger)(const char * str);

  /** The param iess is similar to WDPF point name.  (iess is shortcat
      for Identifier of Enterprise Server Signal ) return -1 for no
      exist point , < -1 for error and >=0 for good point Stored in
      library as: findByIESS */
  typedef long (*LiveEDSFindByIESS)(p_LiveEDSConnection connection,
                                    const char* iess);

  /** Similiar to findByIESS but performs two searches.
      First is exactly the same like in findByIESS (case sensitive).
      If this search has no results, second search is performed
      (case insensitive).
      Stored in library as: findByIESS_NoCase */
  typedef long (*LiveEDSFindByIESS_NoCase)(p_LiveEDSConnection connection,
                                           const char * iess );

  /** Usualy iess (the name of EDS point similar to WDPF point name)
      is used to get lid.  In same cases better may by used idcs and
      zd name of EDS point, which is privided by this function. (For
      exmple if idcs are shorted than iess ) (idcs is shortcat for
      Identifier of Digital Control System ) return -1 for no exist
      point , < -1 for error and >=0 for good point Stored in
      library as: findByIDCS*/
  typedef long (*LiveEDSFindByIDCS)(p_LiveEDSConnection connection,
                                    const char* idcs, const char * zd);

  /** Similiar to findByIDCS but performs two searches.
      First is exactly the same like in findByIDCS (case sensitive).
      If this search has no results, second search is performed
      (case insensitive).
      Stored in library as: findByIDCS_NoCase */
  typedef long (*LiveEDSFindByIDCS_NoCase)(p_LiveEDSConnection connection,
                                           const char * idcs, const char * zd );

  /** Returns points SID - used for accesing archival data*/
  typedef long (*LiveEDSGetSID)(p_LiveEDSConnection conn, long lid);

  /** Must set this function before any read().  Cannot write points
      which are marked as Input(to read) by this function.  Is able
      to call this function more than ones for one lid.  return 0
      for ok, !=0 for error Stored in library as: setInput*/
  typedef int (*LiveEDSSetInput)(p_LiveEDSConnection connection, long lid);

  /** Must set this function before any write() of this lid.  Cannot
      read points which are marked as Output(to write) by this
      function.  Is not able to call this function more than ones
      for one lid.  return 0 for ok, !=0 for error. Stored in library
      as: setOutput*/
  typedef int (*LiveEDSSetOutput)(p_LiveEDSConnection connection, long lid);

  /** Point will be no longer refreshed during synchronizeInput.
      Returns 0 for ok, !=0 for error. Stored in library as: unsetInput */
  typedef int (*LiveEDSUnsetInput)(p_LiveEDSConnection connection, long lid);

  /** Point will be no longer writen during synchronizeOutput.
      Returns 0 for ok, !=0 for error. Stored in library as: unsetOutput */
  typedef int (*LiveEDSUnsetOutput)(p_LiveEDSConnection connection, long lid);

  /** Must by call before any input operation (read, findBy*) and
      after setInput- reads points value from server return 0 for ok,
      !=0 for error Stored in library as: synchronizeInput*/
  typedef int (*LiveEDSSynchronizeInput)(p_LiveEDSConnection connection);

  /** Reads analog value. Before call this funcion point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      return 0 for ok, !=0 for error Stored in library as:
      readValue */
  typedef int (*LiveEDSReadValue)(p_LiveEDSConnection connection,
                                  long lid, float * val, char * qual);

  /** Reads double value. Before call this funcion point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      return 0 for ok, !=0 for error Stored in library as:
      readValue */
  typedef int (*LiveEDSReadDouble)(p_LiveEDSConnection connection,
                                   long lid, double * val, char * qual);

  /**  Reads packed value. Before call this funcion point must be
       already set for reading by function setInput, and synchronized
       with server using synchronizeInput.
       return 0 for ok, !=0 for error. Stored in library as:
       readPacked*/
  typedef int (*LiveEDSReadPacked)(p_LiveEDSConnection connection,
                                   long lid, unsigned long* val, char* qual);

  /**  Reads 64bit integer value. Before call this funcion point must be
       already set for reading by function setInput, and synchronized
       with server using synchronizeInput.
       return 0 for ok, !=0 for error. Stored in library as:
       readPacked*/
  typedef int (*LiveEDSReadInt64)(p_LiveEDSConnection connection,
                                  long lid, int64_t * val, char* qual);

  /** Reads binary value. Before call this funcion point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      return 0 for ok, !=0 for error Stored in library as:
      readBinary*/
  typedef int (*LiveEDSReadBinary)(p_LiveEDSConnection connection,
                                   long lid, unsigned char* val, char* qual);

  /** Returns field id for given field name, or 0 if no such field exists.
      Works only with EDS standard fields.
      Stored in library as: fieldIdFromName */
  typedef int (*LiveEDSFieldIdFromName)(const char* name);
  typedef int (*LiveEDSFieldIdFromWDPFName)(const char* name);

  /** Reads integer field value. For dynamic fields point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      return 0 for ok, !=0 for error. Stored in library as:
      readFieldInt */
  typedef int (*LiveEDSReadFieldInt)(p_LiveEDSConnection connection,
                                     long lid,
                                     int field_id,
                                     int * val);

  /** Reads analog field value. For dynamic fields point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      return 0 for ok, !=0 for error. Stored in library as:
      readFieldDouble */
  typedef int (*LiveEDSReadFieldValue)(p_LiveEDSConnection connection,
                                       long lid,
                                       int field_id,
                                       float * val);

  /** Reads double field value. For dynamic fields point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      return 0 for ok, !=0 for error. Stored in library as:
      readFieldDouble */
  typedef int (*LiveEDSReadFieldDouble)(p_LiveEDSConnection connection,
                                        long lid,
                                        int field_id,
                                        double * val);

  /** Reads string field value and stores it in buffer.
      For dynamic fields point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      return 0 for ok, !=0 for error. Stored in library as:
      readFieldString */
  typedef int (*LiveEDSReadFieldString)(p_LiveEDSConnection connection,
                                        long lid,
                                        int field_id,
                                        char * buffer,
                                        int buffer_size);

  /** Reads integer field value. For dynamic fields point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      return 0 for ok, !=0 for error. Stored in library as:
      readFieldInt */
  typedef int (*LiveEDSReadFieldIntByName)(p_LiveEDSConnection connection,
                                           long lid,
                                           const char * field_name,
                                           int * val);

  typedef int (*LiveEDSReadFieldIntByWDPFName)(p_LiveEDSConnection connection,
                                               long lid,
                                               const char * field_name,
                                               int * val);

  /** Reads analog field value. For dynamic fields point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      return 0 for ok, !=0 for error. Stored in library as:
      readFieldDouble */
  typedef int (*LiveEDSReadFieldValueByName)(p_LiveEDSConnection connection,
                                             long lid,
                                             const char *field_id,
                                             float * val);

  typedef int (*LiveEDSReadFieldValueByWDPFName)(p_LiveEDSConnection connection,
                                                 long lid,
                                                 const char *field_id,
                                                 float * val);

  /** Reads double field value. For dynamic fields point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      return 0 for ok, !=0 for error. Stored in library as:
      readFieldDouble */
  typedef int (*LiveEDSReadFieldDoubleByName)(p_LiveEDSConnection connection,
                                              long lid,
                                              const char * field_name,
                                              double * val);

  typedef int (*LiveEDSReadFieldDoubleByWDPFName)(p_LiveEDSConnection connection,
                                                  long lid,
                                                  const char * field_name,
                                                  double * val);

  /** Reads string field value and stores it in buffer.
      For dynamic fields point must be
      already set for reading by function setInput, and synchronized
      with server using synchronizeInput.
      return 0 for ok, !=0 for error. Stored in library as:
      readFieldString */
  typedef int (*LiveEDSReadFieldStringByName)(p_LiveEDSConnection connection,
                                              long lid,
                                              const char *field_name,
                                              char * buffer,
                                              int buffer_size);

  typedef int (*LiveEDSReadFieldStringByWDPFName)(p_LiveEDSConnection connection,
                                                  long lid,
                                                  const char *field_name,
                                                  char * buffer,
                                                  int buffer_size);

  /** Writes point's ST field value.
      Point must be set for output.
      Return 0 for ok, != for error. Stored in library as: writeStatus */
  typedef int (*LiveEDSWriteStatus)(p_LiveEDSConnection connection,
                                    long lid,
                                    unsigned int value,
                                    unsigned int mask);

  /** Writes point's XSTn field value, where n can be on of {1,2,3}.
      Point must be set for output.
      Return 0 for ok, != for error. Stored in library as: writeXSTn */
  typedef int (*LiveEDSWriteXSTn)(p_LiveEDSConnection connection,
                                  long lid,
                                  int n,
                                  int value,
                                  int mask);

  /** Writes analog value. Before call to this funcion point must be
      already inited by setOutput.
      return 0 for ok, !=0 for error Stored in library as:
      writeValue*/
  typedef int (*LiveEDSWriteValue)(p_LiveEDSConnection connection,
                                   long lid, float * val, char * qual);

  /** Writes double value. Before call to this funcion point must be
      already inited by setOutput.
      return 0 for ok, !=0 for error Stored in library as:
      writeValue*/
  typedef int (*LiveEDSWriteDouble)(p_LiveEDSConnection connection,
                                    long lid, double * val, char * qual);

  /** Writes packed value. Before call to this funcion point must be
      already inited by setOutput.
      return 0 for ok, !=0 for error Stored in library as:
      writePacked*/
  typedef int (*LiveEDSWritePacked)(p_LiveEDSConnection connection,
                                    long lid, unsigned long* val, char* qual);

  /** Writes int64 value. Before call to this funcion point must be
      already inited by setOutput.
      return 0 for ok, !=0 for error Stored in library as:
      writePacked*/
  typedef int (*LiveEDSWriteInt64)(p_LiveEDSConnection connection,
                                   long lid, int64_t* val, char* qual);

  /** Writes binary value. Before call to this funcion point must be
      already inited by setOutput.
      return 0 for ok, !=0 for error Stored in library as:
      writeBinary*/
  typedef int (*LiveEDSWriteBinary)(p_LiveEDSConnection connection,
                                    long lid, unsigned char* val, char* qual);

  /**  Must by called after all write*() calls
       and before next synchronizeInput().
       Return 0 for ok, !=0 for error.
       Stored in library as: SynchronizeOutput*/
  typedef int  (*LiveEDSSynchronizeOutput)(p_LiveEDSConnection connection);

  /** Returns highest LID of the point set*/
  typedef int (*LiveEDSHighestLID)(p_LiveEDSConnection connection);
  /** Return number of points in the point set*/
  typedef int (*LiveEDSPointCount)(p_LiveEDSConnection connection);
  /**Returns technological group id of a given point*/
  // typedef int (*LiveEDSTechnologicalGroup)(p_LiveEDSConnection connection, long lid); // ess_group_t? TODO
  /**Returns security group id of a given point*/
  // typedef int (*LiveEDSTechnologicalGroup)(p_LiveEDSConnection connection, long lid); // ess_group_t? TODO
  /**Checks whether a given point is alive, i.e. not deleted*/
  typedef bool (*LiveEDSIsPointAlive)(p_LiveEDSConnection connection, long lid);
  /**Returns quality of a given point*/
  typedef char (*LiveEDSPointQuality)(p_LiveEDSConnection connection, long lid);
  /**Returns IESS of a given point*/
  typedef const char* (*LiveEDSPointIESS)(p_LiveEDSConnection connection, long lid);
  /**Returns ZD of a given point*/
  typedef const char* (*LiveEDSPointZD)(p_LiveEDSConnection connection, long lid);
  /**Returns IDCS of a given point*/
  typedef const char* (*LiveEDSPointIDCS)(p_LiveEDSConnection connection, long lid);
  /**Returns DESC of a given point*/
  typedef const char* (*LiveEDSPointDESC)(p_LiveEDSConnection connection, long lid);
  /**Returns AUX of a given point*/
  typedef const char* (*LiveEDSPointAUX)(p_LiveEDSConnection connection, long lid);
  /**Returns AR of a given point*/
  typedef char (*LiveEDSPointAR)(p_LiveEDSConnection connection, long lid);
  /**Returns RT of a given point - string version*/
  typedef const char* (*LiveEDSPointRTString)(p_LiveEDSConnection connection, long lid);
  /**Returns RT of a given point - id version*/
  typedef char (*LiveEDSPointRTId)(p_LiveEDSConnection connection, long lid);
  /**Returns the value of a given point in a string of an appropriate format - depending on the point type*/
  typedef const char* (*LiveEDSPointValue)(p_LiveEDSConnection connection, long lid);
  /**Checks whether an update is required*/
  typedef bool (*LiveEDSIsUpdateRequired)(p_LiveEDSConnection connection);
  /**Checks whether static info has changed*/
  typedef bool (*LiveEDSStaticInfoChanged)(p_LiveEDSConnection connection);
  /**Checks whether dynamic info has changed*/
  typedef bool (*LiveEDSDynamicInfoChanged)(p_LiveEDSConnection connection);
  /**Returns technological groups
     Deprecated, use pointTechGroups instead*/
  typedef const byte* (*LiveEDSPointGroups)(p_LiveEDSConnection connection, long lid);
  /**Returns security groups*/
  typedef const byte* (*LiveEDSPointSecGroups)(p_LiveEDSConnection connection, long lid);
  /**Returns technological groups*/
  typedef const byte* (*LiveEDSPointTechGroups)(p_LiveEDSConnection connection, long lid);

  /** Returns new connection structure - but does not connect.
      This structure must be destroyed using destroyConnection
      Stored in library as: newConnection*/
  typedef p_LiveEDSConnection (*LiveEDSNewConnection)();

  /** Disconnects and destroys connection structure
      Stored in library as: destroyConnection*/
  typedef void (*LiveEDSDestroyConnection)(p_LiveEDSConnection connection);

  /** Structure that represents this library - contains all functions
      pointers and if created using getLiveEDSLib than pointers are
      initiated properly*/
  typedef struct
  {
    LiveEDSInit init;
    LiveEDSAuthInit authInit;
    LiveEDSSetupLogger setupLogger;
    LiveEDSFindByIESS findByIESS;
    LiveEDSFindByIESS_NoCase findByIESS_NoCase;
    LiveEDSFindByIDCS findByIDCS;
    LiveEDSFindByIDCS_NoCase findByIDCS_NoCase;
    LiveEDSGetSID getSID;
    LiveEDSSetInput setInput;
    LiveEDSSetOutput setOutput;
    LiveEDSUnsetInput unsetInput;
    LiveEDSUnsetOutput unsetOutput;
    LiveEDSSynchronizeInput synchronizeInput;
    LiveEDSReadValue readValue;
    LiveEDSReadDouble readDouble;
    LiveEDSReadPacked readPacked;
    LiveEDSReadInt64 readInt64;
    LiveEDSReadBinary readBinary;
    LiveEDSFieldIdFromName fieldIdFromName;
    LiveEDSFieldIdFromWDPFName fieldIdFromWDPFName;
    LiveEDSReadFieldInt readFieldInt;
    LiveEDSReadFieldValue readFieldValue;
    LiveEDSReadFieldDouble readFieldDouble;
    LiveEDSReadFieldString readFieldString;
    LiveEDSReadFieldIntByName readFieldIntByName;
    LiveEDSReadFieldIntByWDPFName readFieldIntByWDPFName;
    LiveEDSReadFieldValueByName readFieldValueByName;
    LiveEDSReadFieldValueByWDPFName readFieldValueByWDPFName;
    LiveEDSReadFieldDoubleByName readFieldDoubleByName;
    LiveEDSReadFieldDoubleByWDPFName readFieldDoubleByWDPFName;
    LiveEDSReadFieldStringByName readFieldStringByName;
    LiveEDSReadFieldStringByWDPFName readFieldStringByWDPFName;
    LiveEDSWriteXSTn writeXSTn;
    LiveEDSWriteValue writeValue;
    LiveEDSWriteDouble writeDouble;
    LiveEDSWritePacked writePacked;
    LiveEDSWriteInt64 writeInt64;
    LiveEDSWriteBinary writeBinary;
    LiveEDSSynchronizeOutput synchronizeOutput;
    LiveEDSHighestLID highestLID;
    LiveEDSPointCount pointCount;
    LiveEDSIsPointAlive isPointAlive;
    LiveEDSPointQuality pointQuality;
    LiveEDSPointIESS pointIESS;
    LiveEDSPointZD pointZD;
    LiveEDSPointIDCS pointIDCS;
    LiveEDSPointDESC pointDESC;
    LiveEDSPointAUX pointAUX;
    LiveEDSPointAR pointAR;
    LiveEDSPointRTString pointRTString;
    LiveEDSPointRTId pointRTId;
    LiveEDSPointValue pointValue;
    LiveEDSIsUpdateRequired isUpdateRequired;
    LiveEDSStaticInfoChanged staticInfoChanged;
    LiveEDSDynamicInfoChanged dynamicInfoChanged;
    LiveEDSPointGroups pointGroups;
    LiveEDSPointSecGroups pointSecGroups;
    LiveEDSPointTechGroups pointTechGroups;
    LiveEDSNewConnection newConnection;
    LiveEDSDestroyConnection destroyConnection;
    LiveEDSWriteStatus writeStatus;
  } LiveEDSLib;

/* This version should be manually updated after changes in library iface */
#define LIVE_EDS_LIB_VERSION "9.1 LIVE_API=1"

  /** Returns pointer to static structure (it shouldn't be destroyed
      by user) containing pointers to all library functions.  Param
      value is for recognizing if header file is compatibile with
      library and allways should be set to LIVE_EDS_LIB_VERSION. This
      is only function which have to be loaded manualy from library
      - user can load other functions or just call this and use
      getLiveEDSLib structure*/
  typedef LiveEDSLib* (*GetLiveEDSLib)(const char* version);


#if defined(__CPPLUS) || defined(__CPLUSPLUS) || defined(__cplusplus)
} // extern "C"
#endif

#endif //_LIVEEDS_LIB_H_
