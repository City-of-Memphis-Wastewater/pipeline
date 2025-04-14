// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

#include <ctime>
#include <iostream>
#include <iomanip>
#include <string>
#include <memory>
#include <vector>
#include <sstream>

#include <boost/date_time/posix_time/posix_time.hpp>

#include "../liveeds2/liveeds.h"
#include "../archeds2/archeds.h"

#include "../liveeds2/liveeds.cpp"
#include "../archeds2/archeds.cpp"

using namespace std;

int init(LiveEDS& live, ArchEDS& arch, const string& remoteHost, int srvPort, int archPort)
{
  int err = 0;

  err = live.init(edsRead, "0.0.0.0", 0, remoteHost.c_str(), srvPort, 0, 32768);

  if (err) {
    cout << "Failed to initialize LiveEDS" << endl;
    return err;
  }

  err = arch.init("0.0.0.0", 0, remoteHost.c_str(), archPort, 0, 32768);

  if (err) {
    cout << "Failed to initialize ArchEDS" << endl;
    return err;
  }

  return 0;
}


int testArch(LiveEDS& live,
             ArchEDS& arch,
             time_t start,
             long range,
             short step,
             size_t numPoints,
             size_t offset,
             bool verbose)
{
  vector<long> sids(numPoints);
  vector<long> lids(numPoints);

  ostringstream iessgen;
  for (size_t p = 0; p < numPoints; ++p) {
    iessgen.clear();
    iessgen.str(string());
    iessgen << "ANALOG_R_" << setfill('0') << setw(6) << (p + offset);

    lids[p] = live.findByIESS(iessgen.str().c_str());
    sids[p] = live.getSID(lids[p]);

    // cout << lids[p] << '\t' << sids[p] << endl; // TODO: remove
  }

  boost::posix_time::ptime time_stamp = boost::posix_time::microsec_clock::universal_time();

  for (size_t p = 0; p < numPoints; ++p) {
    EDSTabTrend_ptr tab = arch.getTabTrend(sids[p], "VALUE");
    arch.addTabTrend(tab);
  }

  arch.executeTabTrends(static_cast<long>(start), static_cast<long>(range), static_cast<long>(step), true);

  ArchEDSTrendRow *row = arch.fetchTabTrendRow();

  while (row) {

    if (verbose) {
      for (size_t i = 0; i < row->count; ++i)
        cout << row->points[i].val << ' ' << row->points[i].qual << ";\t";
      cout << endl;
    }

    arch.destroyTrendRow(row);
    row = arch.fetchTabTrendRow();
  }

  boost::posix_time::time_duration benchmark = boost::posix_time::microsec_clock::universal_time() - time_stamp;
  clog << "\ntime: " << benchmark.total_seconds() << '.'
       << setfill('0') << setw(3) << (benchmark.total_milliseconds() % 1000) << "s" << endl;

  return 0;
}


int main(int argc, char **argv)
{
  if (argc < 7) {
    cout << endl;
    cout << "Usage: " << argv[0] << " remote_address srv_port arch_port start_time range step "
         << "(num_points offset verbose(0 or 1))";
    cout << endl;
    cout << endl;
    cout << "start_time is a non delimited ISO 8601 date and time format: YYYYMMDDTHHMMSS, e.g. 20100908T070605, time is in GMT\n";
    cout << "range and step are in seconds.\n";
    cout << endl;
    return 1;
  }

  time_t start = time(0) - 24 * 3600;
  try {
    static const boost::posix_time::ptime unixEpoch(boost::gregorian::date(1970, 1, 1));
    boost::posix_time::ptime st = boost::posix_time::from_iso_string(argv[4]);
    start = (st - unixEpoch).total_seconds();
  } catch (...) {
    cerr << "Invalid start_time argument." << endl;
    return 1;
  }

  clog << "remote_address: " << argv[1] << '\n';
  clog << "srv_port: " << atoi(argv[2]) << '\n';
  clog << "arch_port: " << atoi(argv[3]) << '\n';
  clog << "start_time: " << asctime(gmtime(&start));
  clog << "range: " << atol(argv[5]) << "s\n";
  clog << "step: " << atoi(argv[6]) << "s\n";

  size_t numPoints = 1000;
  if (argc > 7) {
    numPoints = atoi(argv[7]);
  }
  size_t offset = 0;
  if (argc > 8) {
    offset = atoi(argv[8]);
  }

  if ((numPoints + offset) > 1000) {
    clog << "Resetting num_points and offset to default 1000 and 0" << endl;
    numPoints = 1000;
    offset = 0;
  }

  clog << "num_points: " << numPoints << "\n";
  clog << "offset: " << offset << '\n';

  bool verbose = false;
  if (argc > 9) {
    verbose = (atoi(argv[9]) == 1);
  }
  clog << "verbose: " << verbose << '\n';


  clog << ">>>>>> PRESS ENTER TO START TEST <<<<<<<" << endl;
  cin.get();

  auto live = std::make_unique<LiveEDS>();
  auto arch = std::make_unique<ArchEDS>();

  int err = 0;
  err = init(*live, *arch, argv[1], atoi(argv[2]), atoi(argv[3]));
  if (err)
    return err;

  return testArch(*live,
                  *arch,
                  start,
                  atol(argv[5]),
                  static_cast<short>(atoi(argv[6])),
                  numPoints,
                  offset,
                  verbose);
}
