import fs from "fs";
import path from "path";
import os from "os";

const statusFile = path.resolve(__dirname, "../../status.json");

interface ServiceStatus {
  name: string;
  status: string;
  error?: string;
  time: string;
}

async function checkServices() {
  const services: ServiceStatus[] = [
    { name: "Portal API", status: "UNKNOWN", time: new Date().toISOString() },
    { name: "Docker Engine", status: "UNKNOWN", time: new Date().toISOString() },
  ];

  // Add your actual checks here, example:
  // Ping portal API endpoint
  try {
    // fetch or axios call to your API
    services[0].status = "OK";
  } catch (e) {
    services[0].status = "FAIL";
    services[0].error = e.message;
  }

  // Example Docker Engine check here (local socket or TCP)
  try {
    // ...
    services[1].status = "OK";
  } catch (e) {
    services[1].status = "FAIL";
    services[1].error = e.message;
  }

  const status = {
    timestamp: new Date().toISOString(),
    system: {
      os: `${os.type()} ${os.release()}`,
      uptimeSeconds: os.uptime(),
      memory: {
        totalBytes: os.totalmem(),
        freeBytes: os.freemem(),
      },
    },
    services,
  };

  fs.writeFileSync(statusFile, JSON.stringify(status, null, 2));
  return status;
}

export default checkServices;
