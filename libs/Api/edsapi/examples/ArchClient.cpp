// Niniejsze dane stanowią tajemnicę przedsiębiorstwa.
// The contents of this file is proprietary information.

#ifdef WIN32
#include <windows.h>
#endif

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <memory>

// EDS LiveClient header file
#include <LiveClient.h>

// EDS ArchClient header file
#include <ArchClient.h>

// Some common types are defined in eds namespace
using namespace eds;
// LiveClient is in eds::live namespace
using namespace eds::live;
// ArchClient is in eds::arch namespace
using namespace eds::arch;


LiveClient* initializeLiveClient(const char* version,
                                 const char* host,
                                 unsigned short port)
{
  try
  {
    printf("Creating LiveClient for EDS version %s...\n", version);
    std::auto_ptr<LiveClient> client(new LiveClient(version));

    // Initialize in read mode
    printf("Initializing LiveClient connection to %s:%u...\n", host, port);
    client->init(AccessMode_Read,
                 "0.0.0.0",       // bind to all local interfaces
                 0,               // bind to any local port
                 host,
                 port,
                 50);

    printf("LiveClient initialized successfully!\n");
    return client.release();
  }
  catch (const BackendNotFoundError& exc)
  {
    // Couldn't load backend. Requested version might be incorrect,
    // or 'edsapi_live_*' library might be missing.
    printf("Couldn't load live backend library for EDS %s (%s)\n",
      version, exc.what());
    return 0;
  }
  catch (const LiveClientError& exc)
  {
    printf("Couldn't initialize live client connection object (%s)\n",
      exc.what());
    return 0;
  }
}

int sidFromPointName(LiveClient* client, const char* pointName)
{
  try
  {
    int lid = client->findByIESS(pointName);
    if (lid == -1)
    {
      printf("Couldn't find point with IESS '%s'\n", pointName);
      return -1;
    }

    return client->pointSID(lid);
  }
  catch (const Error& exc)
  {
    printf("Failed to resolve server id from point name '%s' (%s)\n",
      pointName, exc.what());
    return -1;
  }
}


ArchClient* initializeArchClient(const char* version,
                                 const char* host,
                                 unsigned short port)
{
  try
  {
    printf("Creating ArchClient for EDS version %s...\n", version);
    std::auto_ptr<ArchClient> client(new ArchClient(version));

    // Initialize as client (read mode)
    printf("Initializing ArchClient connection to %s:%u...\n", host, port);
    client->init("0.0.0.0", // bind to all local interfaces
                 0,         // bind to any local port
                 host,
                 port,
                 50);

    printf("ArchClient initialized successfully!\n");
    return client.release();
  }
  catch (const BackendNotFoundError& exc)
  {
    // Couldn't load backend. Requested version might be incorrect,
    // or 'edsapi_arch_*' library might be missing.
    printf("Couldn't load arch backend library for EDS %s (%s)\n",
      version, exc.what());
    return 0;
  }
  catch (const ArchClientError& exc)
  {
    printf("Couldn't initialize arch client connection object (%s)\n",
      exc.what());
    return 0;
  }
}

void executeReports(ArchClient* client, int maxSid, int avgSid)
{
  try
  {
    printf("Executing reports...\n");

    // Pointers are wrapped in auto_ptr to automatically release objects
    // in case of exception.
    std::auto_ptr<ReportFunction> maxFunction(
      client->getReportFunction("MAX_VALUE"));
    std::auto_ptr<ReportFunction> avgFunction(
      client->getReportFunction("AVG"));

    time_t now = time(0);

    // Calculate maximum for point maxSid over last 24 hours.
    maxFunction->pushPointParam(maxSid);
    maxFunction->pushTimestampParam(now - 24 * 3600);
    maxFunction->pushTimestampParam(now);

    // Calculate average for point avgSid over last 24 hours.
    // Shades will have priority over values from archive.
    avgFunction->pushPointParam(avgSid, 0xFF, ShadeMode_PreferShade);
    avgFunction->pushTimestampParam(now - 24 * 3600);
    avgFunction->pushTimestampParam(now);

    int maxQuery = client->addQuery(maxFunction.get());
    int avgQuery = client->addQuery(avgFunction.get());

    // This function will block until reports are ready
    client->executeQueries();

    // Fetch and display report results
    char quality;

    printf("Report results:\n");
    double maxValue = client->getResponse(maxQuery, &quality);
    printf("MAX_VALUE(sid=%d) = %f%c\n", maxSid, maxValue, quality);

    double avgValue = client->getResponse(avgQuery, &quality);
    printf("AVG(sid=%d) = %f%c\n", avgSid, avgValue, quality);
  }
  catch (const Error& exc)
  {
    printf("Failed to execute report functions (%s)\n", exc.what());
  }
}

void writeShades(ArchClient* client, int sid1, int sid2)
{
  try
  {
    printf("Writing shades...\n");

    time_t now = time(0);

    // Write 10.0G for last 5 hours
    client->addShadeValue(sid1,
                          now - 5 * 3600,
                          now,
                          10.0,
                          Quality_Good);
    // Write 20.0G for range <-5 hours; -2 hours>
    client->addShadeValue(sid2,
                          now - 5 * 3600,
                          now - 2 * 3600 - 1,
                          20.0,
                          Quality_Good);
    // Write 40.0 for range <-2 hours; +5 hours>
    client->addShadeValue(sid2,
                          now - 2 * 3600,
                          now + 5 * 3600,
                          40.0,
                          Quality_Good);

    // This function will block while shades are written
    client->writeShades();

    printf("Shades written successfully!\n");
  }
  catch (const Error& exc)
  {
    printf("Failed to write shades (%s)\n", exc.what());
  }
}

void executeTabularTrends(ArchClient* client, int valueSid, int avgSid)
{
  try
  {
    printf("Executing tabular trends...\n");

    time_t now = time(0);

    // Pointers are wrapped in auto_ptr to automatically release objects
    // in case of exception.

    // Create VALUE trend with preference for shade values over archives
    std::auto_ptr<TabularTrend> valueTabTrend(
      client->getTabularTrend(valueSid, "VALUE"));
    client->addTabularTrend(valueTabTrend.get(), ShadeMode_PreferShade);

    // Create AVG trend
    std::auto_ptr<TabularTrend> avgTabTrend(
      client->getTabularTrend(avgSid, "AVG"));
    client->addTabularTrend(avgTabTrend.get());

    // Execute both trends for last 5 hours with 1 hour step size.
    // This function will block until trends are ready.
    client->executeTabularTrends(now - 5 * 3600, 5 * 3600, 3600);

    printf("Tabular trend results:\n");
    printf("VALUE:      \tAVG:        \n");
    TabularTrendRow row;
    while (client->fetchTabularTrendRow(&row))
    {
      for (size_t i = 0; i < row.size(); ++i)
        printf("%12.6f%c\t", row[i].value, row[i].quality);
      printf("\n");
    }
  }
  catch (const Error& exc)
  {
    printf("Failed to write shades (%s)\n", exc.what());
  }
}

int main(int argc, char** argv)
{
  if (argc != 5)
  {
    printf("Usage: %s version rhost srv_port archsrv_port\n", argv[0]);
    return 1;
  }

  const char* version = argv[1];
  const char* rhost = argv[2];
  unsigned short srv_rport = (unsigned short)atoi(argv[3]);
  unsigned short archsrv_rport = (unsigned short)atoi(argv[4]);

  // LiveClient is needed only to resolve point names (IESS) to server ids
  std::auto_ptr<LiveClient> liveClient(
    initializeLiveClient(version, rhost, srv_rport));
  if (liveClient.get() == 0)
    return 2;

  int a1Sid = sidFromPointName(liveClient.get(), "A1");
  int a2Sid = sidFromPointName(liveClient.get(), "A2");
  if (a1Sid < 0 || a2Sid < 0)
    return 3;

  std::auto_ptr<ArchClient> archClient(
    initializeArchClient(version, rhost, archsrv_rport));
  if (archClient.get() == 0)
    return 4;

  executeReports(archClient.get(), a1Sid, a2Sid);
  writeShades(archClient.get(), a1Sid, a2Sid);
  executeTabularTrends(archClient.get(), a1Sid, a2Sid);

  return 0;
}
