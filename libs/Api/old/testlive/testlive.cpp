// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

#include <stdlib.h>
#include <stdio.h>
#if !defined(ESS_WIN32) && !defined(ESS_CYGWIN)
#include <math.h>
#include <time.h>
#endif

#include "../liveeds2/liveeds.h"
#include "../liveeds2/liveeds.cpp"

void ess_sleep( float f )
{
#ifdef ESS_WIN32
  DWORD t;

  t = (DWORD)(f * 1000.0);
  Sleep( t );
#elif defined(ESS_CYGWIN)
  unsigned long t;

  t = (unsigned long)(f * 1e6);
  usleep( t );
#else
  struct timespec t;

  t.tv_sec = (time_t)floor(f);
  t.tv_nsec = (long)((f - floor(f)) * 1000000000.0);
  nanosleep( &t, NULL );
#endif
}

int eds_test_lib(const char * rhost, int rport)
{
  int err;

  long lid_1;
  long lid_2;
  long lid_3;

  LiveEDS* connection = new LiveEDS();

  //connection->setupLogger("debug=7 subsystems=ALL logger=console:7");

  err = connection->init( edsReadWrite,
                          "0.0.0.0",0,
                          rhost,rport,0,32768);

  if( err != EDS_LIB_NO_ERROR ) {
    printf( "init() returned %d\n", err );
    return err;
  }

  // start of initialize points
  lid_1 = connection->findByIESS_NoCase( "0_IesS" );
  lid_2 = connection->findByIESS_NoCase( "110_IESS" );
  lid_3 = connection->findByIESS_NoCase( "150_iEss" );

  printf("lid_1 = %ld\n",lid_1);
  printf("lid_2 = %ld\n",lid_2);
  printf("lid_3 = %ld\n",lid_3);

  err = connection->setInput(lid_3);
  err = connection->setInput(lid_2);

  err = connection->setOutput(lid_1);
  // end of initialize points

  int field_id = connection->fieldIdFromName("UN");
  char buf[30];

  int z;
  for(z=0; z<=5; z++) {
    float value;
    char quality;

    err = connection->synchronizeInput();
    if( err != EDS_LIB_NO_ERROR ) {
      printf("synchronizeInput() returned %d\n",err);
      if( err == EDS_LIB_ERR_PROTOCOL_MISMATCH ) {
        delete connection;
        return err;
      }
    }

    // start of calculation loop:
    err |= connection->readField( lid_3, "IESS", buf, 30);
    printf("lid=%ld IESS=%s\n",lid_3,buf);
    err |= connection->read( lid_3, &value, &quality );
    printf("lid=%ld value=%f%c\n",lid_3,value,quality);
    err |= connection->readField(lid_3,field_id,buf,30);
    printf("lid=%ld UN=%s\n",lid_3,buf);
    err |= connection->readField(lid_3,"T",buf,30);
    printf("lid=%ld T=%s\n",lid_3,buf);

    err |= connection->readField( lid_2, "IESS", buf, 30);
    printf("lid=%ld IESS=%s\n",lid_2,buf);
    err |= connection->read( lid_2, &value, &quality );
    printf("lid=%ld value=%f%c\n",lid_2,value,quality);
    err |= connection->readField(lid_2,field_id,buf,30);
    printf("lid=%ld UN=%s\n",lid_2,buf);
    err |= connection->readField(lid_2,"T",buf,30);
    printf("lid=%ld T=%s\n",lid_2,buf);

    value = (float)z;
    quality = 'G';

    err |= connection->write( lid_1, &value, &quality );
    err |= connection->writeXSTn(lid_1, 1, z);

    // ...
    // end of calculation loop

    if(err) {
      printf("err = %d\n",err);
      delete connection;
      return err;
    }

    err = connection->synchronizeOutput();
    if( err != EDS_LIB_NO_ERROR) {
      printf("synchronizeOutput() returned %d\n",err);
      if( err == EDS_LIB_ERR_PROTOCOL_MISMATCH ) {
        delete connection;
        return err;
      }
    }

    ess_sleep(1.0);
  }

  //end:;

  connection->shut();

  delete connection;

  return 0;
}

int main(int argc, char** argv)
{
  if(argc!=3) {
    printf("Usage: %s rhost rport\n", argv[0] );
    return 1;
  }
  printf(">>>>>>>>>>>>> TO START TEST PRESS ENTER <<<<<<<<<<<<\n");
  getchar();
  return eds_test_lib(argv[1],atoi(argv[2]));
}
