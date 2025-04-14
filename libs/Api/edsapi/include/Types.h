// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

/**
 * \file
 * Common type definitions
 */

#ifndef EDSAPI_TYPES_H
#define EDSAPI_TYPES_H

/// Main namespace containing all EDS API definitions
namespace eds
{

#ifndef word
typedef unsigned short word;        ///< 16 bit unsigned int
#endif

#ifndef dword
typedef unsigned int dword;         ///< 32 bit unsigned int
#endif

#ifndef llong
#if defined(_WIN32) || defined(__WIN32__)
typedef __int64 llong;              ///< 64 bit signed int
#else
typedef long long llong;            ///< 64 bit signed int
#endif
#endif

#ifndef ddword
#if defined(_WIN32) || defined(__WIN32__)
typedef unsigned __int64 ddword;    ///< 64 bit unsigned int
#else
typedef unsigned long long ddword;  ///< 64 bit unsigned int
#endif
#endif


/// Point quality
enum Quality : char
{
  Quality_None    = 'N',
  Quality_Good    = 'G',
  Quality_Fair    = 'F',
  Quality_Poor    = 'P',
  Quality_Bad     = 'B',
  Quality_FltOut  = 'O',
};

}

#endif
