// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

/**
 * \file
 * Client for archive data
 *
 * \example ArchClient.cpp
 */

#ifndef EDS_ARCHCLIENT_H
#define EDS_ARCHCLIENT_H

#include <ctime>
#include <string>
#include <vector>
#include "Errors.h"
#include "Types.h"

struct EDSArchConnection;
struct EDSArchFunction;
struct EDSArchTabTrend;

namespace eds
{

namespace detail
{
  class Backend;
}


/// Namespace for all archive client related classes
namespace arch
{

/// Archive / shade download preference
enum ShadeMode
{
  ShadeMode_PreferRegular = 0x00,   ///< Prefer archive values over shades
  ShadeMode_PreferShade   = 0x01,   ///< Prefer shades over archive values
  ShadeMode_OnlyRegular   = 0x02,   ///< Use only archive values
  ShadeMode_OnlyShade     = 0x03,   ///< Use only shades
};

/// ArchClient's error codes
enum ArchErrorCode
{
  ArchErrorCode_NoError             = 0,      ///< No error occured
  ArchErrorCode_InvalidResult       = -20,    ///< Backend function returned invalid result
  ArchErrorCode_BadConnectionObject = -200,   ///< Invalid connection object
  ArchErrorCode_NoSuchFunction      = -201,   ///< Invalid report function
  ArchErrorCode_ShadeWriteFailed    = -202,   ///< Failed to write shade
  ArchErrorCode_NoConnection        = -203,   ///< No connection to server
  ArchErrorCode_BadParams           = -204,   ///< Invalid report function arguments
  ArchErrorCode_ProtocolMismatch    = -205,   ///< Client-server protocol mismatch
  ArchErrorCode_RequestError        = -206,   ///< Request has failed (see API logs)
  ArchErrorCode_AccessDenied        = -207,   ///< Server rejected login attempt
};


class ReportFunction;
class TabularTrend;
struct PointValue;

/// Identifier of report query
typedef int QueryId;

/**
 * Row of tabular trend result data
 *
 * Each element of this vector represents a single value of a point in trend
 * (vector values correspond to trend columns).
 */
typedef std::vector<PointValue> TabularTrendRow;

template <typename FunctionPtr>
struct Function;


/**
 * Archive data client
 *
 * Objects of this class allow retrieval and updating of archive data
 * stored on EDS Archive Server.
 *
 * ArchClient supports three different types of archive objects:
 *  - reports - provide raw or aggregated historical data for a specific moment
 *              in time (single timestamp)
 *  - tabular trends - provide raw or aggregated historical data for a specific
 *                     time interval (timestamp range)
 *  - shades - allow to provide alternative historical data (through
 *             substitution or extension of actual archived data)
 *
 * ArchClient allows to queue several requests of the same type and execute
 * them in batches.
 * However, simultaneously registering requests for different types of archive
 * objects is not supported. Always call clear() before requesting ArchClient
 * to work on a different type of archive object.
 *
 * Only one archive backend can be loaded at any time. Do not create multiple
 * ArchClient objects with different values of \em version parameter.
 * Multiple ArchClient objects with the same \em version are allowed.
 *
 * Most methods of this class may throw exceptions:
 *  - ArchClientError - backend library returned an error.
 *    Use ArchClientError::errorCode() to get more information on error type.
 *  - UninitializedClientError - initializeAsAgent() or initializeAsUser()
 *    method was not called or ArchClient was disconnected using shut() method.
 *  - UnsupportedFunctionError - called method is not supported by currently
 *    loaded backend. This usually happens when feature was not available in
 *    that particular EDS version.
 *
 * Methods of this class are not thread safe and can be called from one
 * thread only.
 */
class ArchClient
{
public:
  /**
   * Creates an archive client for specified server version
   *
   * \param[in] version - version of backend to load
   *                      (in dotted notation, e.g. \em "9.1")
   * \exception BackendNotFoundError - thrown when specified backend could
   *                                   not be loaded
   */
  explicit ArchClient(const char* version);
  ~ArchClient();

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
   * Initializes connection to an archive server
   *
   * \param[in] lhost - local host (specify \em "0.0.0.0" to bind to all
   *                    local network interfaces)
   * \param[in] lport - local port (specify \em 0 to bind to any free port)
   * \param[in] rhost - Archive Server host to connect to
   * \param[in] rport - Archive Server port to connect to (typically \em 43001)
   * \param[in] lport_range - if \p lport is already taken, try binding with up
   *                          to \p lport_range ports higher than that port number
   * \param[in] max_packet - maximum allowed UDP packet size (sometimes needed
   *                         to circumvent network routing limitations)
   *
   * \deprecated Use initializeAsAgent() instead.
   */
  void init(const char* lhost,
            word lport,
            const char* rhost,
            word rport,
            word lport_range,
            word max_packet = 32767);

  /**
   * Initializes connection to an archive server with key pair as credentials.
   *
   * \param[in] program_name - name of the program using the API
   *                           (identifies the connection during authentication)
   * \param[in] instance_name - name of the program instance
   *                            (identifies the connection during authentication)
   * \param[in] lhost - local host (specify \em "0.0.0.0" to bind to all
   *                    local network interfaces)
   * \param[in] lport - local port (specify \em 0 to bind to any free port)
   * \param[in] rhost - Archive Server host to connect to
   * \param[in] rport - Archive Server port to connect to (typically \em 43001)
   * \param[in] lport_range - if \p lport is already taken, try binding with up
   *                          to \p lport_range ports higher than that port number
   * \param[in] max_packet - maximum allowed UDP packet size (sometimes needed
   *                         to circumvent network routing limitations)
   * \since EDS 9.2
   *
   * This method can initialize connection to any version of archive server.
   * However, when connecting to servers older than 9.2, it will ignore \p program_name and
   * \p instance_name parameters and use the default agent credentials instead:
   *  - program_name="api"
   *  - instance_name="default"
   */
  void initializeAsAgent(const char* program_name,
                         const char* instance_name,
                         const char* lhost,
                         word lport,
                         const char* rhost,
                         word rport,
                         word lport_range,
                         word max_packet = 32767);

  /**
   * Initializes connection to an archive server with login and password as credentials.
   *
   * \param[in] user_name - user's name
   * \param[in] password - user's password
   * \param[in] lhost - local host (specify \em "0.0.0.0" to bind to all
   *                    local network interfaces)
   * \param[in] lport - local port (specify \em 0 to bind to any free port)
   * \param[in] rhost - Archive Server host to connect to
   * \param[in] rport - Archive Server port to connect to (typically \em 43001)
   * \param[in] lport_range - if \p lport is already taken, try binding with up
   *                          to \p lport_range ports higher than that port number
   * \param[in] max_packet - maximum allowed UDP packet size (sometimes needed
   *                         to circumvent network routing limitations)
   * \since EDS 9.2
   *
   * This method is implemented in backends since version 9.2.
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
   * Closes connection to Archive Server
   *
   *
   * No methods except initializeAsAgent() / initializeAsUser() / init()
   * may be called afterwards.
   */
  void shut();

  /**
   * Discards all previously created requests from ArchClient
   *
   *
   * This method must be called when switching between different types
   * of archive objects (i.e. reports, trends and shades).
   */
  void clear();

  /**
   * Creates a ReportFunction object for a specific raw or aggregate
   * Archive Server function
   *
   * \param[in] name - name of archive function to create
   *                   (e.g. \em VALUE, \em AVG).
   *                   Please consult EDS Terminal documentation for a list
   *                   of available archive functions (remove the leading '@'
   *                   character from function name).
   * \return new ReportFunction object
   *
   * Ownership of the created ReportFunction object is transferred to
   * the caller. It must be released using the \p delete operator.
   */
  ReportFunction* getReportFunction(const char* name);

  /**
   * Enqueues a report function for execution
   *
   * \param[in] function - report function to execute
   * \return report query identifier for fetching result
   *
   * Passed ReportFunction object must be already initialized
   * with appropriate report parameters.
   */
  QueryId addQuery(ReportFunction* function);
  /**
   * Reads result (value, quality) from given report query id
   *
   * \param[in] id - report query identifier
   * \param[out] quality - quality of returned value
   *                       (typically one of eds::Quality enumerations)
   * \return calculated value of report function
   *
   * Note that this function may be called only when executeQueries()
   * finished successfully.
   */
  double getResponse(QueryId id, char* quality);
  /**
   * Executes all queued report functions
   *
   */
  void executeQueries();
  /**
   * Queues, executes and gets response from a single report function
   *
   * \param[in] function - report function to execute
   * \param[out] quality - quality of returned value
   *                       (typically one of eds::Quality enumerations)
   * \return calculated value of report function
   *
   * This is a convenience overload which combines functionality of
   * addQuery(), executeQueries() and getResponse() into a single method.
   */
  double executeQuery(ReportFunction* function, char* quality);

  /**
   * Creates a TabularTrend object for a specific point and archive function
   *
   * \param[in] sid - server identifier of point.
   *                  Server identifiers can be obtained using
   *                  eds::live::LiveClient::pointSID() method.
   * \param[in] function - name of base archive function to use in tabular trend
   *                       (e.g. \em VALUE, \em AVG).
   *                       Please consult EDS Terminal documentation for a list
   *                       of available archive functions (remove the leading
   *                       '@' character from function name).
   * \return new TabularTrend object
   *
   * Ownership of the created TabularTrend object is transferred to
   * the caller. It must be released using the \p delete operator.
   */
  TabularTrend* getTabularTrend(int sid, const char* function);
  /**
   * Enqueues a tabular trend for execution
   *
   * \param[in] trend - tabular trend to execute
   * \param[in] shade_mode - specifies preference for regular archive values
   *                         or shades
   *
   * Passed TabularTrend object must be already initialized
   * with appropriate parameters.
   */
  void addTabularTrend(TabularTrend* trend,
                       unsigned char shade_mode = ShadeMode_PreferRegular);
  /**
   * Executes all queued tabular trends
   *
   * \param[in] ref_time - reference time (timestamp) for which to execute
   *                       the tabular trend. This is usually the first
   *                       timestamp of requested range.
   * \param[in] range - total length (in seconds) of time range to fetch
   * \param[in] step - length (in seconds) of a single step
   *
   * Archive Server will calculate <tt>(range / step)</tt> tabular trend rows.
   * ArchClient assumes that <tt>(range % step == 0)</tt>. If this constraint
   * is not satisfied, resulting tabular trend may contain an extra row with
   * undefined contents.
   */
  void executeTabularTrends(std::time_t ref_time, long range, long step);
  /**
   * Fetches a row of data from tabular trend and advances to the next row
   *
   * \param[out] row - trend row object to be filled with data
   * \return \p true if row was successfully fetched
   */
  bool fetchTabularTrendRow(TabularTrendRow* row);

  /**
   * Enqueues a shade to be written
   *
   * \param[in] sid - server identifier of point.
   *                  Server identifiers can be obtained using
   *                  eds::live::LiveClient::pointSID() method.
   * \param[in] start_ts - first timestamp of time range to write
   * \param[in] end_ts - last timestamp of time range to write
   * \param[in] value - value to write
   * \param[in] quality - quality to write
   */
  void addShadeValue(int sid,
                     std::time_t start_ts,
                     std::time_t end_ts,
                     float value,
                     char quality);
  /**
   * Writes all queued shades
   *
   */
  void writeShades();

private:
  // non-copyable
  ArchClient(const ArchClient&);
  ArchClient& operator =(const ArchClient&);

  template <typename FunctionPtr>
  void initializeFunction(Function<FunctionPtr>& function,
                          const std::string& functionName);
  template <typename FunctionPtr>
  void checkFunction(const Function<FunctionPtr>& function) const;

  template <typename FunctionPtr>
  void throwUnsupportedFunction(const Function<FunctionPtr>& function) const;

  eds::detail::Backend* _backend;
  struct FunctionTable* _functions;
  EDSArchConnection* _connection;
};


/**
 * Represents a report function with its parameters
 *
 * Depending on their type (\em VALUE, \em AVG, etc.) report functions expect
 * different number and types of parameters. Please consult EDS Terminal
 * documentation for more information on function arguments.
 */
class ReportFunction
{
public:
  ~ReportFunction();

  /**
   * Pushes a point argument to function
   *
   * \param[in] sid - server identifier of point.
   *                  Server identifiers can be obtained using
   *                  eds::live::LiveClient::pointSID() method.
   * \param[in] bits_filter - when other than 0xFF, enables bit filter.
   *                          Bit filter only works for PACKED and BINARY points.
   *                          It rejects all archive values which do not have the
   *                          \p bits_filter bit set.
   * \param[in] shade_mode - specifies preference for regular archive values
   *                         or shades
   */
  void pushPointParam(int sid,
                      unsigned char bits_filter = 0xFF,
                      unsigned char shade_mode = ShadeMode_PreferRegular);
  /**
   * Pushes a timestamp argument to function
   *
   */
  void pushTimestampParam(std::time_t ts);
  /**
   * Pushes a floating point (double) argument to function
   *
   */
  void pushValueParam(double v);

  /**
   * Removes all pushed arguments from function
   *
   */
  void clearParams();

private:
  // non-copyable
  ReportFunction(const ReportFunction&);
  ReportFunction& operator=(const ReportFunction&);

  // constructed by ArchClient
  ReportFunction(eds::detail::Backend* backend,
                 struct FunctionTable* functions,
                 EDSArchFunction* archFunction);

  template <typename FunctionPtr>
  void checkFunction(const Function<FunctionPtr>& function) const;

  eds::detail::Backend* _backend;
  struct FunctionTable* _functions;
  EDSArchFunction* _internalFunction;

  friend class ArchClient;
};


/**
 * Point value (sample)
 *
 * Represents value and quality of a process point at some specific time.
 */
struct PointValue
{
  std::time_t ts;   ///< Timestamp
  std::time_t tss;  ///< Timestamp shift
  double value;     ///< Point value
  char quality;     ///< Point quality
};


/**
 * Represents a tabular trend with its parameters
 *
 * Depending on their type (\em VALUE, \em AVG, etc.) tabular trend functions
 * expect a different number of parameters. Please consult EDS Terminal
 * documentation for more information on tabular trend arguments.
 */
class TabularTrend
{
public:
  ~TabularTrend();

  /**
   * Pushes a floating point (double) argument to tabular trend
   *
   */
  void pushParam(double v);

  /**
   * Removes all pushed arguments from tabular trend
   *
   */
  void clearParams();

private:
  // non-copyable
  TabularTrend(const TabularTrend&);
  TabularTrend& operator=(const TabularTrend&);

  // constructed by ArchClient
  TabularTrend(eds::detail::Backend* backend,
               struct FunctionTable* functions,
               EDSArchTabTrend* archTabTrend);

  template <typename FunctionPtr>
  void checkFunction(const Function<FunctionPtr>& function) const;

  eds::detail::Backend* _backend;
  struct FunctionTable* _functions;
  EDSArchTabTrend* _internalTabTrend;

  friend class ArchClient;
};


/**
 * Thrown when backend library returns an error.
 */
class ArchClientError : public Error
{
public:
  /// \private
  ArchClientError(int errorCode);

  /**
   * Numeric %error code
   *
   * \return Typically one of eds::arch::ArchErrorCode enumerations will be returned.
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
