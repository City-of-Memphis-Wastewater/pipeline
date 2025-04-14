// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

/**
 * \file
 * Point status (ST) bit definitions
 */

#ifndef EDSAPI_POINT_STATUS_H
#define EDSAPI_POINT_STATUS_H

#include "Types.h"

/// Main namespace containing all EDS API definitions
namespace eds
{

/// Point status bits
enum StatusBit : dword
{
  ST_ALARM_BETTER        = 0x00000001, ///< Alarm condition is improving
  ST_ALARM_WORSE         = 0x00000002, ///< Alarm condition is worsening
  ST_ALARM_LOW           = 0x00000004, ///< Alarm LOW (both HIGH and LOW produce SENSOR Alarm)
  ST_ALARM_HIGH          = 0x00000008, ///< Alarm HIGH (both HIGH and LOW produce SENSOR Alarm)
  ST_ALARM_SUPPRESSED    = 0x00000010, ///< Alarm is suppressed
  ST_ALARM_UNACK         = 0x00000020, ///< Alarm is unacknowledged
  ST_ALARM_CUTOUT        = 0x00000040, ///< Alarm is cutout
  ST_ALARM_ON            = 0x00000080, ///< Alarm is active
  ST_QUALITY_GOOD        = 0x00000000, ///< Good value quality
  ST_QUALITY_FAIR        = 0x00000100, ///< Fair value quality
  ST_QUALITY_POOR        = 0x00000200, ///< Poor value quality
  ST_QUALITY_BAD         = 0x00000300, ///< Bad value quality
  ST_ALARM_STALE         = 0x00000400, ///< Failed to read all alarm data from the remote system (e.g. Alarm Timestamp)
  ST_OFFSCAN             = 0x00000800, ///< Point is in OFF-SCAN mode, i.e. Server ignores updates from data feeders
  //RESERVED             = 0x00001000,
  ST_VIRTUAL             = 0x00002000, ///< (internal EDS use)
  ST_NOVALUE             = 0x00004000, ///< (internal EDS use)
  ST_TIMEDOUT            = 0x00008000, ///< Point value has timed-out, is not updated in EDS Server
  ST_ALARM_PRIORITY      = 0x00070000, ///< Bits 16, 17 and 18 carry Alarm Priority (1-8) dectemented by 1
  //RESERVED             = 0x00080000, 
  ST_ALARM_NUMBER        = 0x00700000, ///< Bits 20, 21 and 22 carry Alarm Number (1-4) dectemented by 1
  //RESERVED             = 0x00800000, 
  //RESERVED             = 0x01000000, 
  //RESERVED             = 0x02000000,
  ST_NOACCESS            = 0x04000000, ///< EDS Server cannot respond with point value due to user's limited access (Security Groups) 
  ST_REM_OFFSCAN         = 0x08000000, ///< The point is in OFF-SCAN mode in the remote system
  ST_FORCE_ARCHIVE       = 0x10000000, ///< (internal EDS use)
  ST_REM_ERROR           = 0x20000000, ///< (internal EDS use)
  ST_ALARM_TOGGLED       = 0x40000000, ///< (internal EDS use)
  ST_REM_TIMEDOUT        = 0x80000000  ///< Point is timed-out in the remote system
};

}

#endif // EDSAPI_POINT_STATUS_H
