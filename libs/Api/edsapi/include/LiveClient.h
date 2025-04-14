// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

/**
 * \file
 * Client for live data
 *
 * \example LiveClient.cpp
 */

#ifndef EDS_LIVECLIENT_H
#define EDS_LIVECLIENT_H

#include <stdint.h>

#include <string>
#include <vector>
#include "Errors.h"
#include "Types.h"

struct EDSLiveConnection;

namespace eds
{

namespace detail
{
  class Backend;
}


/// Namespace for all live client related classes
namespace live
{

/// LiveClient's mode of operation
enum AccessMode
{
  AccessMode_Read       = 0x01,
  AccessMode_Write      = 0x10,
  AccessMode_ReadWrite  = (AccessMode_Read | AccessMode_Write),
};

/// Process point type
enum PointType : char
{
  PointType_Analog    = 'A',
  PointType_Binary    = 'B',
  PointType_Packed    = 'P',
  PointType_Double    = 'D',
  PointType_Int64     = 'I',
};

/// Process point's archiving mode
enum ArchiveType : char
{
  ArchiveType_None      = 'N',
  ArchiveType_LongTerm  = 'L',
  ArchiveType_External  = 'E',
  ArchiveType_FillIn    = 'F',
};

/// LiveClient's error codes
enum LiveErrorCode
{
  LiveErrorCode_NoError             = 0,      ///< No error occured
  LiveErrorCode_InvalidResult       = -10,    ///< Backend function returned invalid result
  LiveErrorCode_BadConnectionObject = -100,   ///< Invalid connection object
  LiveErrorCode_UninitializedSocket = -101,   ///< Failed to initialize socket
  LiveErrorCode_UninitializedAgent  = -102,   ///< Failed to initialize agent
  LiveErrorCode_ProtocolMismatch    = -103,   ///< Client-server protocol mismatch
  LiveErrorCode_AccessDenied        = -104,   ///< Server rejected login attempt
  LiveErrorCode_NotLoggedIn         = -105,   ///< Client is still connecting
  LiveErrorCode_NotSynchronized     = -106,   ///< Client is still synchronizing with server
  LiveErrorCode_ResponseTimeout     = -107,   ///< Server failed to respond in time
  LiveErrorCode_BidirectionalPoint  = -108,   ///< Attempted to set the same point as input and output
};


/**
 * Identifier of process point field
 *
 * Fields of process points have both string names and
 * numeric identifiers (FieldIds).
 * Referencing point names using identifiers is more efficient.
 *
 * Use LiveClient::fieldIdFromName() and LiveClient::fieldIdFromWDPFName()
 * methods to convert field names to identifiers.
 */
typedef int FieldId;

/**
 * Bit vector of point groups
 *
 * Point groups are identified by a 0-based index, with
 * the \em admin group having index 0.
 *
 * Currently 256 groups are defined, although this number might
 * increase in future versions of EDS.
 */
typedef std::vector<bool> PointGroups;

template <typename FunctionPtr>
struct Function;


/**
 * Live data client
 *
 * Objects of this class allow retrieval and updating of live process
 * point parameters.
 *
 * Only one live backend can be loaded at any time. Do not create multiple
 * LiveClient objects with different values of \em version parameter.
 * Multiple LiveClient objects with the same \em version are allowed.
 *
 * Most methods of this class may throw exceptions:
 *  - LiveClientError - backend library returned an error.
 *    Use LiveClientError::errorCode() to get more information on error type.
 *  - UninitializedClientError - initializeAsAgent() or initializeAsUser()
 *    method was not called or LiveClient was disconnected using shut() method.
 *  - UnsupportedFunctionError - called method is not supported by currently
 *    loaded backend. This usually happens when feature was not available in
 *    that particular EDS version.
 *
 * Methods of this class are not thread safe and can be called from one
 * thread only.
 */
class LiveClient
{
public:
  /**
   * Creates a live client for specified server version
   *
   * \param[in] version - version of backend to load
   *                      (in dotted notation, e.g. \em "9.1")
   * \exception BackendNotFoundError - thrown when specified backend could
   *                                   not be loaded
   */
  explicit LiveClient(const char* version);
  ~LiveClient();

  /**
   * Initializes logger parameters
   *
   * \param[in] str - options string for logger (using common EDS syntax)
   *
   * The options string follows the same format used in all EDS applications.
   * For example, to log all messages to console, pass the following
   * parameter string:
   * <tt>"debug=7 subsystems=ALL logger=console:7"</tt>.
   */
  void setupLogger(const char* str);

  /**
   * Initializes connection to a live server
   *
   * \param[in] access_mode - one of eds::live::AccessMode enumerations
   * \param[in] lhost - local host (specify \em "0.0.0.0" to bind to all
   *                    local network interfaces)
   * \param[in] lport - local port (specify \em 0 to bind to any free port)
   * \param[in] rhost - Server host to connect to
   * \param[in] rport - Server port to connect to (typically \em 43000)
   * \param[in] lport_range - if \p lport is already taken, try binding with up
   *                          to \p lport_range ports higher than that port number
   * \param[in] max_packet - maximum allowed UDP packet size (sometimes needed
   *                         to circumvent network routing limitations)
   *
   * \deprecated Use initializeAsAgent() instead.
   *
   * If this method throws a LiveClientError exception with any of the
   * following error codes:
   *  - LiveErrorCode_NotLoggedIn
   *  - LiveErrorCode_NotSynchronized
   *
   * then it is possible to continue using this LiveClient instance.
   * These errors are temporary and may be resolved by calling
   * synchronizeInput() method (possibly multiple times).
   */
  void init(int access_mode,
            const char* lhost,
            word lport,
            const char* rhost,
            word rport,
            word lport_range,
            word max_packet = 32767);

  /**
   * Initializes connection to a live server with key pair as credentials.
   *
   * \param[in] access_mode - one of eds::live::AccessMode enumerations
   * \param[in] program_name - name of the program using the API
   *                           (identifies the connection during authentication)
   * \param[in] instance_name - name of the program instance
   *                            (identifies the connection during authentication)
   * \param[in] lhost - local host (specify \em "0.0.0.0" to bind to all
   *                    local network interfaces)
   * \param[in] lport - local port (specify \em 0 to bind to any free port)
   * \param[in] rhost - Server host to connect to
   * \param[in] rport - Server port to connect to (typically \em 43000)
   * \param[in] lport_range - if \p lport is already taken, try binding with up
   *                          to \p lport_range ports higher than that port number
   * \param[in] max_packet - maximum allowed UDP packet size (sometimes needed
   *                         to circumvent network routing limitations)
   * \since EDS 9.2
   *
   * This method can initialize connection to any version of live server.
   * However, when connecting to servers older than 9.2, it will ignore \p program_name and
   * \p instance_name parameters and use the default agent credentials instead:
   *  - program_name="api"
   *  - instance_name="default"
   *
   * If this method throws a LiveClientError exception with any of the
   * following error codes:
   *  - LiveErrorCode_NotLoggedIn
   *  - LiveErrorCode_NotSynchronized
   *
   * then it is possible to continue using this LiveClient instance.
   * These errors are temporary and may be resolved by calling
   * synchronizeInput() method (possibly multiple times).
   */
  void initializeAsAgent(AccessMode access_mode,
                         const char* program_name,
                         const char* instance_name,
                         const char* lhost,
                         word lport,
                         const char* rhost,
                         word rport,
                         word lport_range,
                         word max_packet = 32767);

  /**
   * Initializes connection to a live server with login and password as credentials.
   *
   * \param[in] user_name - user's name
   * \param[in] password - user's password
   * \param[in] lhost - local host (specify \em "0.0.0.0" to bind to all
   *                    local network interfaces)
   * \param[in] lport - local port (specify \em 0 to bind to any free port)
   * \param[in] rhost - Server host to connect to
   * \param[in] rport - Server port to connect to (typically \em 43000)
   * \param[in] lport_range - if \p lport is already taken, try binding with up
   *                          to \p lport_range ports higher than that port number
   * \param[in] max_packet - maximum allowed UDP packet size (sometimes needed
   *                         to circumvent network routing limitations)
   * \since EDS 9.2
   *
   * This method is implemented in backends since version 9.2.
   *
   * The connection is initialized in read mode. When point samples must be sent to a live server,
   * use initializeAsAgent() method instead.
   *
   * If this method throws a LiveClientError exception with any of the
   * following error codes:
   *  - LiveErrorCode_NotLoggedIn
   *  - LiveErrorCode_NotSynchronized
   *
   * then it is possible to continue using this LiveClient instance.
   * These errors are temporary and may be resolved by calling
   * synchronizeInput() method (possibly multiple times).
   */
  void initializeAsUser(const char* user_name,
                        const char* password,
                        const char* lhost,
                        word lport,
                        const char* rhost,
                        word rport,
                        word lport_range,
                        word max_packet = 32767);

  /**
   * Closes connection to Server
   *
   *
   * No methods except initializeAsAgent() / initializeAsUser() / init()
   * may be called afterwards.
   */
  void shut();

  /**
   * Returns local id of point identified by IESS
   *
   * \param[in] iess - point's IESS
   * \return local id of point or \em -1 if point could not be found
   */
  int findByIESS(const char* iess);

  /**
   * Returns local id of point identified by IESS
   *
   * \param[in] iess - point's IESS
   * \return local id of point or \em -1 if point could not be found
   *
   * Similar to findByIESS but performs two searches. First is exactly
   * the same as in findByIESS (case sensitive). If this search yields
   * no results, a second, case insensitive search is performed.
   */
  int findByIESSNoCase(const char* iess);

  /**
   * Returns local id of point identified by IDCS and ZD
   *
   * \param[in] idcs - point's IDCS
   * \param[in] zd - point's ZD
   * \return local id of point or \em -1 if point could not be found
   *
   * IDCS is an abbreviation for Identifer of Digital Control System.
   */
  int findByIDCS(const char* idcs, const char* zd);

  /**
   * Returns local id of point identified by IDCS and ZD
   *
   * \param[in] idcs - point's IDCS
   * \param[in] zd - point's ZD
   * \return local id of point or \em -1 if point could not be found
   *
   * IDCS is an abbreviation for Identifer of Digital Control System.
   *
   * Similar to findByIDCS but performs two searches. First is exactly
   * the same as in findByIDCS (case sensitive). If this search yields
   * no results, a second, case insensitive search is performed.
   */
  int findByIDCSNoCase(const char* idcs, const char* zd);

  /**
   * Returns highest local point id for current connection.
   *
   */
  int highestLID();

  /**
   * Returns number of points for current connection.
   *
   * \remark This is not necessarily equal to highestLid(), since some
   *         local ids might be unused.
   */
  int pointCount();

  /**
   * Checks whether point is alive
   *
   * \return \p true if point is not deleted and if \p lid is in range
   * <tt>\<0; highestLID()\></tt>
   */
  bool isPointAlive(int lid);

  /**
   * Registers LiveClient as receiver of dynamic values for given point.
   *
   *
   * Points must be marked as input to receive updates of dynamic fields
   * (value, quality, status) from server.
   * Note that static point fields (IESS, DESC, AUX) can be read without
   * calling this method.
   *
   * LiveClient internally uses a counter which is incremented by every
   * invocation of setInput(). This means that every call to setInput() must
   * be paired with a call to unsetInput() on the same point.
   *
   * LiveClient must be in AccessMode_Read or AccessMode_ReadWrite access
   * mode to receive point values.
   *
   * It is illegal to mark a point as both input and output.
   */
  void setInput(int lid);

  /**
   * Registers LiveClient as a source of values for given point.
   *
   *
   * Points must be originated (marked as output) to send value updates
   * to server.
   *
   * LiveClient internally uses a counter which is incremented by every
   * invocation of setOutput(). This means that every call to setOutput() must
   * be paired with a call to unsetOutput() on the same point.
   *
   * LiveClient must be in AccessMode_Write or AccessMode_ReadWrite access
   * mode to send point values.
   *
   * It is illegal to mark a point as both input and output.
   */
  void setOutput(int lid);

  /**
   * Unregisters LiveClient from receiving point value updates.
   *
   *
   * LiveClient internally uses a counter which is decremented by every
   * invocation of unsetInput(). This means that every call to setInput() must
   * be paired with a call to unsetInput() on the same point.
   */
  void unsetInput(int lid);

  /**
   * Unregisters LiveClient from sending point value updates.
   *
   *
   * LiveClient internally uses a counter which is decremented by every
   * invocation of unsetOutput(). This means that every call to setOutput() must
   * be paired with a call to unsetOutput() on the same point.
   */
  void unsetOutput(int lid);

  /**
   * Receives updated point values from server
   *
   *
   * This function should be called periodically (typically once per second)
   * in LiveClient's read mode.
   * It downloads updated values for dynamic fields (value, quality, status)
   * of all subscribed points (see setInput()).
   *
   * If this method throws a LiveClientError exception with any of the
   * following error codes:
   *  - LiveErrorCode_NotLoggedIn
   *  - LiveErrorCode_NotSynchronized
   *
   * then it is possible to continue using this LiveClient instance.
   * These errors are temporary and may be resolved by calling
   * synchronizeInput() method again (possibly multiple times).
   */
  void synchronizeInput();

  /**
   * Sends updated point values to server
   *
   *
   * This function should be called periodically (typically once per second)
   * LiveClient's write mode.
   * It sends updated values for dynamic fields (value, quality, status)
   * of all originated points (see setOutput()).
   */
  void synchronizeOutput();

  /**
   * Checks if LiveClient's point list requires an update
   *
   *
   * If this method returns \p true, call synchronizeInput() to download
   * updated point values from server.
   */
  bool isUpdateRequired();

  /**
   * Checks if static part of point list has changed
   *
   *
   * This method returns \p true if the static part of point list has changed
   * on the server.
   * This happens when a value of a static point field was modified, or when
   * a point was added / deleted.
   *
   * To get updated value of this flag, call synchronizeInput().
   *
   * \attention Calling staticInfoChanged() automatically resets value of this
   *            flag to \p false.
   */
  bool staticInfoChanged();

  /**
   * Checks if dynamic part of point list has changed
   *
   *
   * This method returns \p true if the dynamic part of point list has changed
   * on the server.
   * This happens when a value of a dynamic point field (value, quality, status)
   * has changed.
   *
   * To get updated value of this flag, call synchronizeInput().
   *
   * \attention Calling dynamicInfoChanged() automatically resets value of this
   *            flag to \p false.
   */
  bool dynamicInfoChanged();

  /**
   * Returns quality of point
   *
   * \return Typically one of eds::Quality enumerations will be returned.
   *         This is not guaranteed however for future backend versions.
   */
  char pointQuality(int lid);

  /**
   * Returns server identifier of point
   *
   *
   * Use this method to convert local point identifiers to server point
   * identifiers.
   */
  int pointSID(int lid);

  /**
   * Returns IESS of point
   *
   */
  std::string pointIESS(int lid);

  /**
   * Returns ZD of point
   *
   */
  std::string pointZD(int lid);

  /**
   * Returns IDCS of point
   *
   */
  std::string pointIDCS(int lid);

  /**
   * Returns DESC (description field) of point
   *
   */
  std::string pointDESC(int lid);

  /**
   * Returns AUX (auxiliary field) of point
   *
   */
  std::string pointAUX(int lid);

  /**
   * Returns full name of point's type
   *
   *
   * Example names are \em "ANALOG", \em "PACKED".
   */
  std::string pointRTString(int lid);

  /**
   * Returns archiving mode of process point
   *
   * \return Typically one of eds::live::ArchiveType enumerations will be returned.
   *         This is not guaranteed however for future backend versions.
   */
  char pointAR(int lid);

  /**
   * Returns type of process point
   *
   * \return Typically one of eds::live::PointType enumerations will be returned.
   *         This is not guaranteed however for future backend versions.
   */
  char pointRT(int lid);

  /**
   * Returns point's value, quality and unit as a string
   *
   *
   * Value is formatted according to point's DP field.
   */
  std::string pointValue(int lid);

  /**
   * Returns point's security groups
   *
   * \return bit array (one bit per security group)
   *
   * Currently 256 groups are defined. Future backend versions may
   * increase this number.
   */
  PointGroups pointSecGroups(int lid);

  /**
   * Returns point's technological groups
   *
   * \return bit array (one bit per technological group)
   *
   * Currently 256 groups are defined. Future backend versions may
   * increase this number.
   */
  PointGroups pointTechGroups(int lid);

  /**
   * Reads analog process point value
   *
   * \param[in] lid - local id of point
   * \param[out] quality - quality of point value (typically one of
   *                       eds::Quality enumerations)
   *
   * Before calling this function, the point must be set for reading
   * (with setInput() function), and synchronized with server
   * (with synchronizeInput()).
   */
  float readAnalog(int lid, char* quality);

  /**
   * Reads double process point value
   *
   * \param[in] lid - local id of point
   * \param[out] quality - quality of point value (typically one of
   *                       eds::Quality enumerations)
   *
   * Before calling this function, the point must be set for reading
   * (with setInput() function), and synchronized with server
   * (with synchronizeInput()).
   */
  double readDouble(int lid, char* quality);

  /**
   * Reads packed process point value
   *
   * \param[in] lid - local id of point
   * \param[out] quality - quality of point value (typically one of
   *                       eds::Quality enumerations)
   *
   * Before calling this function, the point must be set for reading
   * (with setInput() function), and synchronized with server
   * (with synchronizeInput()).
   */
  dword readPacked(int lid, char* quality);

  /**
   * Reads int64 process point value
   *
   * \param[in] lid - local id of point
   * \param[out] quality - quality of point value (typically one of
   *                       eds::Quality enumerations)
   *
   * Before calling this function, the point must be set for reading
   * (with setInput() function), and synchronized with server
   * (with synchronizeInput()).
   */
  llong readInt64(int lid, char* quality);

  /**
   * Reads binary (digital) process point value
   *
   * \param[in] lid - local id of point
   * \param[out] quality - quality of point value (typically one of
   *                       eds::Quality enumerations)
   *
   * Before calling this function, the point must be set for reading
   * (with setInput() function), and synchronized with server
   * (with synchronizeInput()).
   */
  bool readBinary(int lid, char* quality);

  /**
   * Writes analog value to process point
   *
   * \param[in] lid - local id of point
   * \param[in] value - new point value
   * \param[in] quality - new point quality
   *
   * Before calling this function point must be set for writing
   * (with setOutput() function).
   * Updated point values are sent to server during the next
   * synchronizeOutput() call.
   */
  void write(int lid, float value, Quality quality);

  /**
   * Writes double value to process point
   *
   * \param[in] lid - local id of point
   * \param[in] value - new point value
   * \param[in] quality - new point quality
   *
   * Before calling this function point must be set for writing
   * (with setOutput() function).
   * Updated point values are sent to server during the next
   * synchronizeOutput() call.
   */
  void write(int lid, double value, Quality quality);

  /**
   * Writes packed value to process point
   *
   * \param[in] lid - local id of point
   * \param[in] value - new point value
   * \param[in] quality - new point quality
   *
   * Before calling this function point must be set for writing
   * (with setOutput() function).
   * Updated point values are sent to server during the next
   * synchronizeOutput() call.
   */
  void write(int lid, dword value, Quality quality);

  /**
   * Writes int64 value to process point
   *
   * \param[in] lid - local id of point
   * \param[in] value - new point value
   * \param[in] quality - new point quality
   *
   * Before calling this function point must be set for writing
   * (with setOutput() function).
   * Updated point values are sent to server during the next
   * synchronizeOutput() call.
   */
  void write(int lid, llong value, Quality quality);

  /**
   * Writes binary (digital) value to process point
   *
   * \param[in] lid - local id of point
   * \param[in] value - new point value
   * \param[in] quality - new point quality
   *
   * Before calling this function point must be set for writing
   * (with setOutput() function).
   * Updated point values are sent to server during the next
   * synchronizeOutput() call.
   */
  void write(int lid, bool value, Quality quality);

  /**
   * Returns identifier of point's field with specified name
   *
   */
  FieldId fieldIdFromName(const char* name);

  /**
   * Returns identifier of point's WDPF field with specified name
   *
   */
  FieldId fieldIdFromWDPFName(const char* name);

  /**
   * Reads integer field value
   *
   * \param[in] lid - local id of point
   * \param[in] field_id - identifier of point field
   *
   * Before calling this function, the point must be set for reading
   * (with setInput() function), and synchronized with server
   * (with synchronizeInput()).
   */
  int readFieldInt(int lid, FieldId field_id);

  /**
   * Reads float point field value
   *
   * \param[in] lid - local id of point
   * \param[in] field_id - identifier of point field
   *
   * Before calling this function, the point must be set for reading
   * (with setInput() function), and synchronized with server
   * (with synchronizeInput()).
   */
  float readFieldFloat(int lid, FieldId field_id);

  /**
   * Reads double field value
   *
   * \param[in] lid - local id of point
   * \param[in] field_id - identifier of point field
   *
   * Before calling this function, the point must be set for reading
   * (with setInput() function), and synchronized with server
   * (with synchronizeInput()).
   */
  double readFieldDouble(int lid, FieldId field_id);

  /**
   * Reads string field value
   *
   * \param[in] lid - local id of point
   * \param[in] field_id - identifier of point field
   *
   * Before calling this function, the point must be set for reading
   * (with setInput() function), and synchronized with server
   * (with synchronizeInput()).
   */
  std::string readFieldString(int lid, FieldId field_id);

  /**
   * Reads integer field value
   *
   * \param[in] lid - local id of point
   * \param[in] field_name - name of point field
   *
   * This method works similarly to readFieldInt(int, FieldId),
   * but is limited to EDS fields only (it cannot read WDPF fields).
   *
   * Before calling this function, the point must be set for reading
   * (with setInput() function), and synchronized with server
   * (with synchronizeInput()).
   */
  int readFieldInt(int lid, const char* field_name);

  /**
   * Reads float field value
   *
   * \param[in] lid - local id of point
   * \param[in] field_name - name of point field
   *
   * This method works similarly to readFieldFloat(int, FieldId),
   * but is limited to EDS fields only (it cannot read WDPF fields).
   *
   * Before calling this function, the point must be set for reading
   * (with setInput() function), and synchronized with server
   * (with synchronizeInput()).
   */
  float readFieldFloat(int lid, const char* field_name);

  /**
   * Reads double field value
   *
   * \param[in] lid - local id of point
   * \param[in] field_name - name of point field
   *
   * This method works similarly to readFieldDouble(int, FieldId),
   * but is limited to EDS fields only (it cannot read WDPF fields).
   *
   * Before calling this function, the point must be set for reading
   * (with setInput() function), and synchronized with server
   * (with synchronizeInput()).
   */
  double readFieldDouble(int lid, const char* field_name);

  /**
   * Reads string field value
   *
   * \param[in] lid - local id of point
   * \param[in] field_name - name of point field
   *
   * This method works similarly to readFieldString(int, FieldId),
   * but is limited to EDS fields only (it cannot read WDPF fields).
   *
   * Before calling this function, the point must be set for reading
   * (with setInput() function), and synchronized with server
   * (with synchronizeInput()).
   */
  std::string readFieldString(int lid, const char* field_name);

  /**
   * Reads integer WDPF field value
   *
   * \param[in] lid - local id of point
   * \param[in] field_name - name of WPDF point field
   *
   * This method works similarly to readFieldInt(int, FieldId),
   * but is limited to WDPF fields only (it cannot read EDS fields).
   *
   * Before calling this function, the point must be set for reading
   * (with setInput() function), and synchronized with server
   * (with synchronizeInput()).
   */
  int readWDPFFieldInt(int lid, const char* field_name);

  /**
   * Reads float WDPF field value
   *
   * \param[in] lid - local id of point
   * \param[in] field_name - name of WPDF point field
   *
   * This method works similarly to readFieldFloat(int, FieldId),
   * but is limited to WDPF fields only (it cannot read EDS fields).
   *
   * Before calling this function, the point must be set for reading
   * (with setInput() function), and synchronized with server
   * (with synchronizeInput()).
   */
  float readWDPFFieldFloat(int lid, const char* field_name);

  /**
   * Reads double WDPF field value
   *
   * \param[in] lid - local id of point
   * \param[in] field_name - name of WPDF point field
   *
   * This method works similarly to readFieldDouble(int, FieldId),
   * but is limited to WDPF fields only (it cannot read EDS fields).
   *
   * Before calling this function, the point must be set for reading
   * (with setInput() function), and synchronized with server
   * (with synchronizeInput()).
   */
  double readWDPFFieldDouble(int lid, const char* field_name);

  /**
   * Reads string WDPF field value
   *
   * \param[in] lid - local id of point
   * \param[in] field_name - name of WPDF point field
   *
   * This method works similarly to readFieldString(int, FieldId),
   * but is limited to WDPF fields only (it cannot read EDS fields).
   *
   * Before calling this function, the point must be set for reading
   * (with setInput() function), and synchronized with server
   * (with synchronizeInput()).
   */
  std::string readWDPFFieldString(int lid, const char* field_name);

  /**
   * Reads value of point's AT field
   *
   * \param[in] lid - local id of point
   * \param[in] asMicroseconds - default false, returns time from
   *             Jan 1st 1970 00:00:00 GMT
   *               - false: the time is in seconds
   *               - true: the time is in micro-seconds
   *
   * Before calling this function, the point must be set for reading
   * (with setInput() function), and synchronized with server
   * (with synchronizeInput()).
   */
  llong readAT(int lid, bool asMicroseconds = false);

  /**
   * Writes a value to point's AT field
   *
   * \param[in] lid - local id of point
   * \param[in] seconds - seconds since Jan 1st 1970 00:00:00 GMT
   * \param[in] useconds - micro-seconds of the second.
   * \since EDS 9.2
   *
   * Before calling this function, written point must be set for output
   * (see setOutput() function). Updated AT values will be sent
   * to server during the next call to synchronizeOutput().
   */
  void writeAT(int lid, dword seconds, dword useconds);

  /**
   * Writes a value to point's ST field
   *
   * \param[in] lid - local id of point
   * \param[in] value - value containing ST bits to be written (see PointStatus.h)
   * \param[in] mask - bit mask for \p value. Only bits which are set in this
   *                   parameter will be updated.
   * \since EDS 9.2
   *
   * Before calling this function, written point must be set for output
   * (see setOutput() function). Updated ST values will be sent
   * to server during the next call to synchronizeOutput().
   * Bits of the ST field are defined in the header file PointStatus.h
   * - - -
   * **Important notes:**
   *
   *    - bit eds::StatusBit::ST_OFFSCAN cannot be set by this API.
   *
   *    - bits carrying:
   *         * Alarm Pririty (mask 0x00070000, bits 16, 17, 18)
   *         * Alarm Number  (mask 0x00700000, bits 20, 21, 22)
   *      have values decremented by 1 compared to the Alarm Priority or
   *      Alarm Number they are encoding. For example, the following call:
   *
   *            writeST(<lid>, 0x00130088, 0x007700FF);
   *      will set high alarm with attributes:
   *            * Alarm Priority = 4  
   *            * Alarm Number = 2
   *      on Alarm List in EDS Terminal.
   */
  void writeST(int lid, dword value, dword mask);

  /**
   * Writes a value to point's XST<sub>n</sub> field
   *
   * \param[in] lid - local id of point
   * \param[in] n - index of XST field to write.
   *                Currently n can be any value from the <em>{1, 2, 3}</em> set.
   *                Future backend versions may support more XST fields.
   * \param[in] value - value containing XST bits to be written
   * \param[in] mask - bit mask for \p value. Only bits which are set in this
   *                   parameter will be updated.
   * \since EDS 7.3
   *
   * Before calling this function, written point must be set for output
   * (see setOutput() function). Updated XST values will be sent
   * to server during the next call to synchronizeOutput().
   * Fields XSTn are not used internally by EDS - their purpose is to allow
   * a raw bit information from an external system to be available in EDS.
   */
  void writeXSTn(int lid, int n, int value, int mask);

private:
  // non-copyable
  LiveClient(const LiveClient&);
  LiveClient& operator =(const LiveClient&);

  template <typename FunctionPtr>
  void initializeFunction(Function<FunctionPtr>& function, const std::string& functionName);

  template <typename FunctionPtr>
  void checkFunction(const Function<FunctionPtr>& function) const;

  template <typename FunctionPtr>
  void throwUnsupportedFunction(const Function<FunctionPtr>& function) const;

  eds::detail::Backend* _backend;
  struct FunctionTable* _functions;
  EDSLiveConnection* _connection;
};


/**
 * Thrown when backend library returns an error.
 */
class LiveClientError : public Error
{
public:
  /// \private
  LiveClientError(int errorCode);

  /**
   * Numeric %error code
   *
   * \return Typically one of eds::live::LiveErrorCode enumerations will be returned.
   *         This is not guaranteed however, because future backend versions may extend the list
   *         of error codes.
   */
  int errorCode() const
  { return _errorCode; }

private:
  static std::string formatErrorString(int errorCode);

  int _errorCode;
};

}

}

#endif
