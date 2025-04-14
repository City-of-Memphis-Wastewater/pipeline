// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

#include "../liveeds2/liveeds.h"
#include "../archeds2/archeds.h"

#include "../liveeds2/liveeds.cpp"
#include "../archeds2/archeds.cpp"

#include <time.h>
#include <stdlib.h>

int test_archeds2(const char* server, int srv_port, int arch_port)
{
  LiveEDS* live = new LiveEDS();
  ArchEDS* arch = new ArchEDS();

  { // additional block, so auto_ptrs will be deleted properly

//  live->setupLogger("debug=7 subsystems=ALL logger=console:7");
//  arch->setupLogger("debug=7 subsystems=ALL logger=console:7");

    int err = 0;

    err = live->init( edsRead,
                      "0.0.0.0",0,
                      server,srv_port,0,32768);
    if(err) {
      printf("LiveEDS::init failed: %d\n",err);
      return err;
    }

    err = arch->init("0.0.0.0", 0,
                     server, arch_port,
                     0,32768);
    if(err) {
      printf("ArchEDS::init failed: %d\n",err);
      return err;
    }

    long lid_1 = live->findByIESS("0_IESS");
    long lid_2 = live->findByIESS("110_IESS");

    printf("lid_1 = %ld\n",lid_1);
    printf("lid_2 = %ld\n",lid_2);

    long sid_1 = live->getSID(lid_1);
    long sid_2 = live->getSID(lid_2);

    printf("sid_1 = %ld\n",sid_1);
    printf("sid_2 = %ld\n",sid_2);

    EDSFunction_ptr min_1 = arch->getFunction("MIN_VALUE");
    EDSFunction_ptr avg_1 = arch->getFunction("AVG");

    time_t t = time(NULL);

    min_1->pushPointParam(sid_1);
    min_1->pushTimestampParam(static_cast<long>(t-24*3600));
    min_1->pushTimestampParam(static_cast<long>(t));

    avg_1->pushPointParam(sid_2,0xFF,edsPrefereShade);
    avg_1->pushTimestampParam(static_cast<long>(t-24*3600));
    avg_1->pushTimestampParam(static_cast<long>(t));

    int min_id = arch->addQuery(min_1);
    int avg_id = arch->addQuery(avg_1);

    printf("min_id = %d\n",min_id);
    printf("avg_id = %d\n",avg_id);

    arch->executeQueries();

    double val;
    char qual;

    err = arch->getResponse(min_id,&val,&qual);
    if(err) {
      printf("ArchEDS::getResponse for min_id failed: %d\n",err);
      return err;
    }

    printf("MIN_VALUE: %lf%c\n",val,qual);

    err = arch->getResponse(avg_id,&val,&qual);
    if(err) {
      printf("ArchEDS::getResponse for avg_id failed: %d\n",err);
      return err;
    }

    printf("AVG: %lf%c\n",val,qual);

    arch->addShadeValue(sid_1, static_cast<long>(t-5*3600), static_cast<long>(t), 10., 'G');
    arch->addShadeValue(sid_2, static_cast<long>(t-5*3600), static_cast<long>(t-2*3600-1), 20., 'G');
    arch->addShadeValue(sid_2, static_cast<long>(t-2*3600), static_cast<long>(t+5*3600), 40., 'G');

    err = arch->writeShades();
    if(err) {
      printf("ArchEDS::writeShades failed: %d\n",err);
      return err;
    }

    printf("Shades written\n");

    EDSTabTrend_ptr tab_1 = arch->getTabTrend(sid_1, "VALUE");
    EDSTabTrend_ptr tab_2 = arch->getTabTrend(sid_2, "AVG");

    arch->addTabTrend(tab_1, edsPrefereShade);
    arch->addTabTrend(tab_2);

    arch->executeTabTrends(static_cast<long>(t-5*3600), static_cast<long>(5*3600), 600, true);
    printf("VALUE:\tAVG:\n");
    ArchEDSTrendRow* row = arch->fetchTabTrendRow();
    while(row) {
      for(unsigned int i = 0; i < row->count; ++i ) {
        printf("%lf%c\t",row->points[i].val,row->points[i].qual);
      }
      printf("\n");
      arch->destroyTrendRow(row);
      row = arch->fetchTabTrendRow();
    }

  }
  printf("Shutting\n");
  live->shut();
  arch->shut();
  delete live;
  delete arch;
  return 0;
}

int main(int argc, char** argv)
{
  if(argc != 4) {
    printf("Usage: %s eds_server srv_port arch_port\n",argv[0]);
    return 1;
  }
  printf(">>>>>> PRESS ENTER TO START TEST <<<<<<<\n");
  getchar();
  return test_archeds2(argv[1],atoi(argv[2]),atoi(argv[3]));
}
