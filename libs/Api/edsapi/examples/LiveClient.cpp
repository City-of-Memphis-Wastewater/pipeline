// Niniejsze dane stanowi¹ tajemnicê przedsiêbiorstwa.
// The contents of this file is proprietary information.

#ifdef WIN32
#include <windows.h>
#endif

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <memory>

// EDS LiveClient header file
#include <edsapi/include/LiveClient.h>
#include <edsapi/include/PointStatus.h>


// Some common types are defined in eds namespace
using namespace eds;
// LiveClient is in eds::live namespace
using namespace eds::live;


namespace utils
{

void sleep(float seconds)
{
#ifdef WIN32
  DWORD t;

  t = (DWORD)(seconds * 1000.0);
  Sleep(t);
#else
  struct timespec t;

  t.tv_sec = (time_t)floor(seconds);
  t.tv_nsec = (long)((seconds - floor(seconds)) * 1000000000.0);
  nanosleep(&t, NULL);
#endif
}

template <typename T>
T random(T min, T max)
{
  double x = static_cast<double>(rand()) / RAND_MAX;
  T range = max - min;
  return min + static_cast<T>(x * range);
}
} // namespace utils


auto initializeClient(const char* version,
                      const char* instance_name,
                      const char* host,
                      unsigned short port)
{
  try
  {
    printf("Creating LiveClient for EDS version %s...\n", version);
    auto client = std::make_unique<LiveClient>(version);

    // Initialize in bidirectional (read-write) mode
    printf("Initializing LiveClient connection to %s:%u...\n", host, port);
    client->initializeAsAgent(AccessMode_ReadWrite,
                              "edsapi_test",
                              instance_name,
                              "0.0.0.0", // bind to all local interfaces
                              0,         // bind to any local port
                              host,
                              port,
                              50);

    printf("LiveClient initialized successfully!\n");
    return client;
  }
  catch (const BackendNotFoundError& exc)
  {
    // Couldn't load backend. Requested version might be incorrect,
    // or 'edsapi_live_*' library might be missing.
    printf("Couldn't load backend library for EDS %s (%s)\n", version, exc.what());
  }
  catch (const LiveClientError& exc)
  {
    printf("Couldn't initialize client connection object (%s)\n", exc.what());
  }
  std::unique_ptr<LiveClient>{};
}

bool subscribePoint(LiveClient& client, const char* pointName)
{
  try
  {
    // Get lid (local id) of point by it's IESS
    int lid = client.findByIESS(pointName);
    if (lid == -1)
    {
      printf("Couldn't find point with IESS '%s'\n", pointName);
      return false;
    }

    client.setInput(lid);
    return true;
  }
  catch (const Error& exc)
  {
    printf("Failed to subscribe point '%s' (%s)\n", pointName, exc.what());
    return false;
  }
}

bool originatePoint(LiveClient& client, const char* pointName)
{
  try
  {
    // Get lid (local id) of point by it's IESS
    int lid = client.findByIESS(pointName);
    if (lid == -1)
    {
      printf("Couldn't find point with IESS '%s'\n", pointName);
      return false;
    }

    client.setOutput(lid);
    return true;
  }
  catch (const Error& exc)
  {
    printf("Failed to originate point '%s' (%s)\n", pointName, exc.what());
    return false;
  }
}

void downloadPointValues(LiveClient& client)
{
  try
  {
    do
    {
      client.synchronizeInput();
    } while (client.isUpdateRequired());
  }
  catch (const Error& exc)
  {
    printf("Failed to synchronize input point values (%s)\n", exc.what());
  }
}

void printPointValues(LiveClient& client, const char* pointName)
{
  try
  {
    int lid = client.findByIESS(pointName);
    if (lid == -1)
    {
      printf("Couldn't find point with IESS '%s'\n", pointName);
      return;
    }

    // Read string field by name
    std::string iess = client.readFieldString(lid, "IESS");
    printf("lid=%d IESS=%s\n", lid, iess.c_str());

    // Read value of analog point
    char quality;
    float value = client.readAnalog(lid, &quality);
    dword status = client.readFieldInt(lid, "ST");
    int unFieldId = client.fieldIdFromName("UN");
    std::string un = client.readFieldString(lid, unFieldId);

    printf("  value=%f%c [%s], ST=0x%08X\n", value, quality, un.c_str(), status);

    // Read double field
    double bb = client.readFieldDouble(lid, "BB");
    double tb = client.readFieldDouble(lid, "TB");

    printf("  BB=%f TB=%f\n\n", bb, tb);
  }
  catch (const Error& exc)
  {
    printf("Failed to read values of point '%s' (%s)\n", pointName, exc.what());
  }
}

void uploadPointValues(LiveClient& client)
{
  try
  {
    client.synchronizeOutput();
  }
  catch (const Error& exc)
  {
    printf("Failed to synchronize output point values (%s)\n", exc.what());
  }
}

void writePoint(LiveClient& client, const char* pointName, float value, dword status, dword at)
{
  static dword lastStatus;

  try
  {
    int lid = client.findByIESS(pointName);
    if (lid == -1)
    {
      printf("Couldn't find point with IESS '%s'\n", pointName);
      return;
    }

    client.write(lid, value, eds::Quality_Good);
    if (status != lastStatus)
    {
      client.writeST(lid, status, 0x4000FFFF);
      client.writeXSTn(lid, 1, status, 0x0000FFFF);
      client.writeAT(lid, at, 0);
      lastStatus = status;
    }
  }
  catch (const Error& exc)
  {
    printf("Failed to write values of point '%s' (%s)\n", pointName, exc.what());
  }
}

int main(int argc, char** argv)
{
  if (argc != 5)
  {
    printf("Usage: %s version instance_name rhost rport\n", argv[0]);
    return 1;
  }

  const char* version = argv[1];
  const char* instance_name = argv[2];
  const char* rhost = argv[3];
  unsigned short rport = (unsigned short)atoi(argv[4]);

  auto client = initializeClient(version, instance_name, rhost, rport);
  if (!client)
    return 2;

  // Points have to be subscribed to receive value updates from server
  if (!subscribePoint(*client, "A1") || !subscribePoint(*client, "A2"))
    return 3;

  // Points have to be originated to send value changes to server
  if (!originatePoint(*client, "AOut"))
    return 4;

  dword status = ST_ALARM_ON | ST_ALARM_HIGH;
  dword at = static_cast<dword>(time(nullptr));

  // Read and write point values for 60 seconds
  for (int t = 0; t < 60; ++t)
  {
    downloadPointValues(*client);
    printf("------------------------------------------------\n");
    printPointValues(*client, "A1");
    printPointValues(*client, "A2");

    if (!(t % 10))
    {
      at = static_cast<dword>(time(nullptr));
      if (status & ST_ALARM_ON)
        status = 0;
      else
        status = ST_ALARM_ON | ST_ALARM_HIGH;
    }

    writePoint(*client, "AOut", utils::random<float>(0, 1), status, at);
    uploadPointValues(*client);
    printPointValues(*client, "AOut");

    utils::sleep(1.0f);
  }

  return 0;
}
