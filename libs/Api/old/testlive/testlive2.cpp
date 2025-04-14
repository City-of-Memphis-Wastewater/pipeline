// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

#include <stdlib.h>
#include <stdio.h>
#include <time.h>

#include "../liveeds2/liveeds.h"
#include "../liveeds2/liveeds.cpp"

int eds_test_lib(bool write,
                 const char* rhost,
                 int rport,
                 const int iterations,
                 const int points_count,
                 const int offset)
{
  char tmp[50];
  time_t timer;
  int err;
  int* lid_list = new int[offset+points_count];

  LiveEDS* live = new LiveEDS();

  printf("Initial synchronization... ");
  timer = time(NULL);
  err = live->init( edsReadWrite,
                    "0.0.0.0",0,
                    rhost,rport,0,32768);
  if( err != EDS_LIB_NO_ERROR ) {
    printf( "init() returned %d\n", err );
    delete live;
    delete[] lid_list;
    return err;
  }

  err = live->synchronizeInput();
  if( err != EDS_LIB_NO_ERROR ) {
    printf("synchronizeInput() returned %d\n",err);
    if( err == EDS_LIB_ERR_PROTOCOL_MISMATCH ) {
      delete live;
      delete[] lid_list;
      return err;
    }
  }
  printf("done in %ds\n",(int)(time(NULL)-timer));

  if(!write)
  {
    printf("Reading %d points %d times\n", points_count, iterations);
    for(int i=offset; i<offset+points_count; ++i)
    {
      sprintf(tmp,"ANALOG_R_%06d",i);
      lid_list[i] = live->findByIESS(tmp);
      live->setInput(lid_list[i]);
    }

    time_t totalTime = 0;
    for(int i=0; i<iterations; ++i)
    {
      timer = time(NULL);
      printf("Iteration %d/%d\n",i+1,iterations);
      err = live->synchronizeInput();
      if( err != EDS_LIB_NO_ERROR ) {
        printf("synchronizeInput() returned %d\n",err);
        if( err == EDS_LIB_ERR_PROTOCOL_MISMATCH ) {
          delete live;
          delete[] lid_list;
          return err;
        }
      }
      time_t t = time(NULL) - timer;
      totalTime += t;
      float value;
      char quality;
      for(int j=offset; j<offset+points_count; ++j)
      {
        live->readField( lid_list[j], "IESS", tmp, 50);
        live->read( lid_list[j], &value, &quality );
        printf("%s %f%c\n",tmp,value,quality);
      }
    }
    time_t readTotalTime = totalTime;
    float readAvgTime = (totalTime+0.f)/iterations;
    printf("Total time: %ds, avg. per iteration: %fs\n",
           (int)readTotalTime,readAvgTime);
  }
  else
  {
    printf("Writing %d points %d times\n", points_count, iterations);
    for(int i=offset; i<offset+points_count; ++i)
    {
      sprintf(tmp,"ANALOG_W_%06d",i);
      live->unsetInput(lid_list[i]);
      lid_list[i] = live->findByIESS(tmp);
      live->setOutput(lid_list[i]);
    }

    time_t totalTime = 0;
    for(int i=0; i<iterations; ++i)
    {
      timer = time(NULL);
      printf("Iteration %d/%d\n",i+1,iterations);
      float value;
      char quality = 'G';
      for(int j=offset; j<offset+points_count; ++j)
      {
        value = (float)(i + j);
        live->write( lid_list[j], &value, &quality );
        printf("ANALOG_W_%06d = %f\n",j,value);
      }

      err = live->synchronizeOutput();
      if( err != EDS_LIB_NO_ERROR ) {
        printf("synchronizeOutput() returned %d\n",err);
        if( err == EDS_LIB_ERR_PROTOCOL_MISMATCH ) {
          delete live;
          delete[] lid_list;
          return err;
        }
      }
      time_t t = time(NULL) - timer;
      totalTime += t;
    }
    time_t totalWriteTime = totalTime;
    float writeAvgTime = (totalTime+0.f)/iterations;
    printf("Total time: %ds, avg. per iteration: %fs\n",
           (int)totalWriteTime,writeAvgTime);
  }

  delete live;
  delete[] lid_list;

  return 0;
}

int main(int argc, char** argv)
{
  if(argc != 5 && argc!=6 && argc!=7) {
    printf("Usage: %s R/W server_host server_port iterations [points] [offset] \n",
           argv[0] );
    return 1;
  }
  int points = 1000;
  int offset = 0;
  if(argc>5)
  {
    points = atoi(argv[5]);
    if(argc>6)
      offset = atoi(argv[6]);
  }

  if(points > 1000)
    points = 1000;
  if(points + offset > 1000)
    offset = 1000 - points;

  return eds_test_lib(argv[1][0]=='W',
                      argv[2],
                      atoi(argv[3]),
                      atoi(argv[4]),
                      points,
                      offset);
}
