// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

#ifndef EDSAPI_LIVE_BACKEND_H
#define EDSAPI_LIVE_BACKEND_H

#define EDSAPI_LIVE_NO_ERROR                  0
#define EDSAPI_LIVE_ERR_BAD_CONNECTION_OBJECT -100
#define EDSAPI_LIVE_ERR_UNINITIALIZED_SOCKET  -101
#define EDSAPI_LIVE_ERR_UNINITIALIZED_AGENT   -102
#define EDSAPI_LIVE_ERR_PROTOCOL_MISMATCH     -103
#define EDSAPI_LIVE_ERR_ACCESS_DENIED         -104
#define EDSAPI_LIVE_ERR_NOT_LOGGED_IN         -105
#define EDSAPI_LIVE_ERR_NOT_SYNCHRONIZED      -106
#define EDSAPI_LIVE_ERR_RESPONSE_TIMEOUT      -107
#define EDSAPI_LIVE_ERR_BIDIRECTIONAL_POINT   -108

extern "C"
{

/** Structure that represents connection to EDS Server */
struct EDSLiveConnection;
typedef EDSLiveConnection* EDSLiveConnectionPtr;

enum EDSLiveMode
{
  EDSLiveRead = 0x01,
  EDSLiveWrite = 0x10,
  EDSLiveReadWrite = 0x11,
};


/** Initializes connection structure using parameters:
    local host, local port,
    remote host, remote port, max packet size */
typedef int (*EDSLiveInitPtr)(EDSLiveConnectionPtr connection,
                              int mode,
                              const char* lhost, word lport,
                              const char* rhost, word rport,
                              word lport_range,
                              word max_packet);

/** Initializes API in agent mode (authentication will be performed using key pair). */
typedef int (*EDSLiveInitializeAsAgentPtr)(EDSLiveConnectionPtr connection,
                                           int mode,
                                           const char* program_name,
                                           const char* instance_name,
                                           const char* lhost,
                                           word lport,
                                           const char* rhost,
                                           word rport,
                                           word lport_range,
                                           word max_packet);

/** Initializes API in user mode (authentication will be performed with user name and password). */
typedef int (*EDSLiveInitializeAsUserPtr)(EDSLiveConnectionPtr connection,
                                          const char* user_name,
                                          const char* password,
                                          const char* lhost,
                                          word lport,
                                          const char* rhost,
                                          word rport,
                                          word lport_range,
                                          word max_packet);

/** Setups logger using setup string.
    For example: str="debug=7 logger=console:7 subsystems=ALL"*/
typedef void (*EDSLiveSetupLoggerPtr)(const char* str);

/** The param iess is similar to WDPF point name.  (iess is shortcut
    for Identifier of Enterprise Server Signal ) return -1 for no
    exist point, < -1 for error and >=0 for good point Stored in
    library as: findByIESS */
typedef int (*EDSLiveFindByIESSPtr)(EDSLiveConnectionPtr connection,
                                    const char* iess);

/** Similiar to findByIESS but performs two searches.
    First is exactly the same like in findByIESS (case sensitive).
    If this search has no results, second search is performed
    (case insensitive).
    Stored in library as: findByIESS_NoCase */
typedef int (*EDSLiveFindByIESSNoCasePtr)(EDSLiveConnectionPtr connection,
                                          const char* iess);

/** Usualy iess (the name of EDS point similar to WDPF point name)
    is used to get lid.  In same cases better may by used idcs and
    zd name of EDS point, which is privided by this function. (For
    exmple if idcs are shorted than iess ) (idcs is shortcat for
    Identifier of Digital Control System ) return -1 for no exist
    point , < -1 for error and >=0 for good point Stored in
    library as: findByIDCS*/
typedef int (*EDSLiveFindByIDCSPtr)(EDSLiveConnectionPtr connection,
                                    const char* idcs,
                                    const char* zd);

/** Similiar to findByIDCS but performs two searches.
    First is exactly the same like in findByIDCS (case sensitive).
    If this search has no results, second search is performed
    (case insensitive).
    Stored in library as: findByIDCS_NoCase */
typedef int (*EDSLiveFindByIDCSNoCasePtr)(EDSLiveConnectionPtr connection,
                                          const char* idcs,
                                          const char* zd);

/** Returns points SID - used for accesing archival data*/
typedef int (*EDSLivePointSIDPtr)(EDSLiveConnectionPtr conn,
                                  int lid);

/** Must set this function before any read().  Cannot write points
    which are marked as Input(to read) by this function.  Is able
    to call this function more than ones for one lid.  return 0
    for ok, !=0 for error Stored in library as: setInput*/
typedef int (*EDSLiveSetInputPtr)(EDSLiveConnectionPtr connection,
                                  int lid);

/** Must set this function before any write() of this lid.  Cannot
    read points which are marked as Output(to write) by this
    function.  Is not able to call this function more than ones
    for one lid.  return 0 for ok, !=0 for error. Stored in library
    as: setOutput*/
typedef int (*EDSLiveSetOutputPtr)(EDSLiveConnectionPtr connection,
                                   int lid);

/** Point will be no longer refreshed during synchronizeInput.
    Returns 0 for ok, !=0 for error. Stored in library as: unsetInput */
typedef int (*EDSLiveUnsetInputPtr)(EDSLiveConnectionPtr connection,
                                    int lid);

/** Point will be no longer writen during synchronizeOutput.
    Returns 0 for ok, !=0 for error. Stored in library as: unsetOutput */
typedef int (*EDSLiveUnsetOutputPtr)(EDSLiveConnectionPtr connection,
                                     int lid);

/** Must by call before any input operation (read, findBy*) and
    after setInput- reads points value from server return 0 for ok,
    !=0 for error Stored in library as: synchronizeInput*/
typedef int (*EDSLiveSynchronizeInputPtr)(EDSLiveConnectionPtr connection);

/** Reads analog value. Before call this funcion point must be
    already set for reading by function setInput, and synchronized
    with server using synchronizeInput.
    return 0 for ok, !=0 for error Stored in library as:
    readAnalog */
typedef int (*EDSLiveReadAnalogPtr)(EDSLiveConnectionPtr connection,
                                    int lid,
                                    float* val,
                                    char* qual);

/** Reads double value. Before call this funcion point must be
    already set for reading by function setInput, and synchronized
    with server using synchronizeInput.
    return 0 for ok, !=0 for error Stored in library as:
    readDouble */
typedef int (*EDSLiveReadDoublePtr)(EDSLiveConnectionPtr connection,
                                    int lid,
                                    double* val,
                                    char* qual);

/**  Reads packed value. Before call this funcion point must be
     already set for reading by function setInput, and synchronized
     with server using synchronizeInput.
     return 0 for ok, !=0 for error. Stored in library as:
     readPacked*/
typedef int (*EDSLiveReadPackedPtr)(EDSLiveConnectionPtr connection,
                                    int lid,
                                    dword* val,
                                    char* qual);

/**  Reads 64bit integer value. Before call this funcion point must be
     already set for reading by function setInput, and synchronized
     with server using synchronizeInput.
     return 0 for ok, !=0 for error. Stored in library as:
     readPacked*/
typedef int (*EDSLiveReadInt64Ptr)(EDSLiveConnectionPtr connection,
                                   int lid,
                                   llong* val,
                                   char* qual);

/** Reads binary value. Before call this funcion point must be
    already set for reading by function setInput, and synchronized
    with server using synchronizeInput.
    return 0 for ok, !=0 for error Stored in library as:
    readBinary*/
typedef int (*EDSLiveReadBinaryPtr)(EDSLiveConnectionPtr connection,
                                    int lid,
                                    unsigned char* val,
                                    char* qual);

/** Returns field id for given field name, or 0 if no such field exists.
    Works only with EDS standard fields.
    Stored in library as: fieldIdFromName */
typedef int (*EDSLiveFieldIdFromNamePtr)(const char* name);
typedef int (*EDSLiveFieldIdFromWDPFNamePtr)(const char* name);

/** Reads integer field value. For dynamic fields point must be
    already set for reading by function setInput, and synchronized
    with server using synchronizeInput.
    return 0 for ok, !=0 for error. Stored in library as:
    readFieldInt */
typedef int (*EDSLiveReadFieldIntPtr)(EDSLiveConnectionPtr connection,
                                      int lid,
                                      int field_id,
                                      int* val);

/** Reads analog field value. For dynamic fields point must be
    already set for reading by function setInput, and synchronized
    with server using synchronizeInput.
    return 0 for ok, !=0 for error. Stored in library as:
    readFieldFloat */
typedef int (*EDSLiveReadFieldFloatPtr)(EDSLiveConnectionPtr connection,
                                        int lid,
                                        int field_id,
                                        float* val);

/** Reads double field value. For dynamic fields point must be
    already set for reading by function setInput, and synchronized
    with server using synchronizeInput.
    return 0 for ok, !=0 for error. Stored in library as:
    readFieldDouble */
typedef int (*EDSLiveReadFieldDoublePtr)(EDSLiveConnectionPtr connection,
                                         int lid,
                                         int field_id,
                                         double* val);

/** Reads string field value and stores it in buffer.
    For dynamic fields point must be
    already set for reading by function setInput, and synchronized
    with server using synchronizeInput.
    return required size of buffer, <0 for error. Stored in library as:
    readFieldString */
typedef int (*EDSLiveReadFieldStringPtr)(EDSLiveConnectionPtr connection,
                                         int lid,
                                         int field_id,
                                         char* buffer,
                                         int buffer_size);

/** Reads integer field value. For dynamic fields point must be
    already set for reading by function setInput, and synchronized
    with server using synchronizeInput.
    return 0 for ok, !=0 for error. Stored in library as:
    readFieldInt */
typedef int (*EDSLiveReadFieldIntByNamePtr)(EDSLiveConnectionPtr connection,
                                            int lid,
                                            const char* field_name,
                                            int* val);

typedef int (*EDSLiveReadFieldIntByWDPFNamePtr)(EDSLiveConnectionPtr connection,
                                                int lid,
                                                const char* field_name,
                                                int* val);

/** Reads analog field value. For dynamic fields point must be
    already set for reading by function setInput, and synchronized
    with server using synchronizeInput.
    return 0 for ok, !=0 for error. Stored in library as:
    readFieldFloat */
typedef int (*EDSLiveReadFieldFloatByNamePtr)(EDSLiveConnectionPtr connection,
                                              int lid,
                                              const char* field_id,
                                              float* val);

typedef int (*EDSLiveReadFieldFloatByWDPFNamePtr)(EDSLiveConnectionPtr connection,
                                                  int lid,
                                                  const char* field_id,
                                                  float* val);

/** Reads double field value. For dynamic fields point must be
    already set for reading by function setInput, and synchronized
    with server using synchronizeInput.
    return 0 for ok, !=0 for error. Stored in library as:
    readFieldDouble */
typedef int (*EDSLiveReadFieldDoubleByNamePtr)(EDSLiveConnectionPtr connection,
                                               int lid,
                                               const char* field_name,
                                               double* val);

typedef int (*EDSLiveReadFieldDoubleByWDPFNamePtr)(EDSLiveConnectionPtr connection,
                                                   int lid,
                                                   const char* field_name,
                                                   double* val);

/** Reads string field value and stores it in buffer.
    For dynamic fields point must be
    already set for reading by function setInput, and synchronized
    with server using synchronizeInput.
    return required size of buffer, <0 for error. Stored in library as:
    readFieldString */
typedef int (*EDSLiveReadFieldStringByNamePtr)(EDSLiveConnectionPtr connection,
                                               int lid,
                                               const char* field_name,
                                               char* buffer,
                                               int buffer_size);

typedef int (*EDSLiveReadFieldStringByWDPFNamePtr)(EDSLiveConnectionPtr connection,
                                                   int lid,
                                                   const char* field_name,
                                                   char* buffer,
                                                   int buffer_size);

/** Reads point's AT field value.
    Point must be set for input.
    Return 0 for ok, != for error. Stored in library as: readAT */
typedef int (*EDSLiveReadATPtr)(EDSLiveConnectionPtr connection,
                                int lid,
                                dword* seconds,
                                dword* useconds);

/** Writes point's AT field value.
    Point must be set for output.
    Return 0 for ok, != for error. Stored in library as: writeAT */
typedef int (*EDSLiveWriteATPtr)(EDSLiveConnectionPtr connection,
                                 int lid,
                                 dword seconds,
                                 dword useconds);

/** Writes point's ST field value.
    Point must be set for output.
    Return 0 for ok, != for error. Stored in library as: writeST */
typedef int (*EDSLiveWriteSTPtr)(EDSLiveConnectionPtr connection, int lid, dword value, dword mask);

/** Writes point's XSTn field value, where n can be on of {1,2,3}.
    Point must be set for output.
    Return 0 for ok, != for error. Stored in library as: writeXST1 */
typedef int (*EDSLiveWriteXSTnPtr)(EDSLiveConnectionPtr connection,
                                   int lid,
                                   int n,
                                   int value,
                                   int mask);

/** Writes analog value. Before call to this funcion point must be
    already inited by setOutput.
    return 0 for ok, !=0 for error Stored in library as:
    writeAnalog*/
typedef int (*EDSLiveWriteAnalogPtr)(EDSLiveConnectionPtr connection,
                                     int lid,
                                     float val,
                                     char qual);

/** Writes double value. Before call to this funcion point must be
    already inited by setOutput.
    return 0 for ok, !=0 for error Stored in library as:
    writeDouble*/
typedef int (*EDSLiveWriteDoublePtr)(EDSLiveConnectionPtr connection,
                                     int lid,
                                     double val,
                                     char qual);

/** Writes packed value. Before call to this funcion point must be
    already inited by setOutput.
    return 0 for ok, !=0 for error Stored in library as:
    writePacked*/
typedef int (*EDSLiveWritePackedPtr)(EDSLiveConnectionPtr connection,
                                     int lid,
                                     dword val,
                                     char qual);

/** Writes int64 value. Before call to this funcion point must be
    already inited by setOutput.
    return 0 for ok, !=0 for error Stored in library as:
    writePacked*/
typedef int (*EDSLiveWriteInt64Ptr)(EDSLiveConnectionPtr connection,
                                    int lid,
                                    llong val,
                                    char qual);

/** Writes binary value. Before call to this funcion point must be
    already inited by setOutput.
    return 0 for ok, !=0 for error Stored in library as:
    writeBinary*/
typedef int (*EDSLiveWriteBinaryPtr)(EDSLiveConnectionPtr connection,
                                     int lid,
                                     unsigned char val,
                                     char qual);

/**  Must by called after all write*() calls
     and before next synchronizeInput().
     Return 0 for ok, !=0 for error.
     Stored in library as: SynchronizeOutput*/
typedef int  (*EDSLiveSynchronizeOutputPtr)(EDSLiveConnectionPtr connection);

/** Returns highest LID of the point set*/
typedef int (*EDSLiveHighestLIDPtr)(EDSLiveConnectionPtr connection);

/** Return number of points in the point set*/
typedef int (*EDSLivePointCountPtr)(EDSLiveConnectionPtr connection);

/**Checks whether a given point is alive, i.e. not deleted*/
typedef bool (*EDSLiveIsPointAlivePtr)(EDSLiveConnectionPtr connection,
                                       int lid);

/**Returns quality of a given point*/
typedef char (*EDSLivePointQualityPtr)(EDSLiveConnectionPtr connection,
                                       int lid);

/**Returns IESS of a given point*/
typedef const char* (*EDSLivePointIESSPtr)(EDSLiveConnectionPtr connection,
                                           int lid);

/**Returns ZD of a given point*/
typedef const char* (*EDSLivePointZDPtr)(EDSLiveConnectionPtr connection,
                                         int lid);

/**Returns IDCS of a given point*/
typedef const char* (*EDSLivePointIDCSPtr)(EDSLiveConnectionPtr connection,
                                           int lid);

/**Returns DESC of a given point*/
typedef const char* (*EDSLivePointDESCPtr)(EDSLiveConnectionPtr connection,
                                           int lid);


/**Returns AUX of a given point*/
typedef const char* (*EDSLivePointAUXPtr)(EDSLiveConnectionPtr connection,
                                          int lid);

/**Returns AR of a given point*/
typedef char (*EDSLivePointARPtr)(EDSLiveConnectionPtr connection,
                                  int lid);

/**Returns RT of a given point - string version*/
typedef const char* (*EDSLivePointRTStringPtr)(EDSLiveConnectionPtr connection,
                                               int lid);

/**Returns RT of a given point - id version*/
typedef char (*EDSLivePointRTPtr)(EDSLiveConnectionPtr connection,
                                  int lid);

/**Returns the value of a given point in a string of an appropriate format - depending on the point type*/
typedef const char* (*EDSLivePointValuePtr)(EDSLiveConnectionPtr connection,
                                            int lid);

/**Checks whether an update is required*/
typedef bool (*EDSLiveIsUpdateRequiredPtr)(EDSLiveConnectionPtr connection);

/**Checks whether static info has changed*/
typedef bool (*EDSLiveStaticInfoChangedPtr)(EDSLiveConnectionPtr connection);

/**Checks whether dynamic info has changed*/
typedef bool (*EDSLiveDynamicInfoChangedPtr)(EDSLiveConnectionPtr connection);

/**Returns security groups*/
typedef const unsigned char* (*EDSLivePointSecGroupsPtr)(EDSLiveConnectionPtr connection,
                                                         int lid);

/**Returns technological groups*/
typedef const unsigned char* (*EDSLivePointTechGroupsPtr)(EDSLiveConnectionPtr connection,
                                                          int lid);

/** Returns new connection structure - but does not connect.
    This structure must be destroyed using destroyConnection
    Stored in library as: newConnection*/
typedef EDSLiveConnectionPtr (*EDSLiveNewConnectionPtr)();

/** Disconnects and destroys connection structure
    Stored in library as: destroyConnection*/
typedef void (*EDSLiveDestroyConnectionPtr)(EDSLiveConnectionPtr connection);

} // extern "C"

#endif
