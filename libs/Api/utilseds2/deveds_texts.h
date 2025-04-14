// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

#ifndef _DEVEDS_TEXTS_H_
#define _DEVEDS_TEXTS_H_


#if !defined(WIN32) && !defined(_WIN32)
  #define LD_LIBRARY_PATH_TEXT_LOG \
            "Add to the start script or environment this line:\n" \
            "export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/eds/API/C/lib\n"
#else
  #define LD_LIBRARY_PATH_TEXT_LOG \
            "Check if this dll file exists in program directory!\n"
#endif


#endif
