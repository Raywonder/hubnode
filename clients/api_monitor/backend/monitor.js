import axios from "axios";
import fs from "fs";
import path from "path";
import os from "os";

const statusFile = path.resolve(__dirname, "../status.json");

const services = [
  { name: "Portal API", url: "https://portal.tappedin.fm/api/health" },
  { name: "Docker Engine", url: "http://localhost:2375/info" },
  // Add more services here as needed
];

async function checkServices() {
  const serviceStatuses = [];

  for (const service of services) {
    try {
      const res = await axios.get(service.url, { timeout: 3000 });
      serviceStatuses.push({
        name: service.name,
        status: "OK",
        statusCode: res.status,
        time: new Date().toISOString(),
      });
    } catch (err) {
      serviceStatuses.push({
        name: service.name,
        status: "FAIL",
        error: err.message,
        time: new Date().toISOString(),
      });
    }
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
    services: serviceStatuses,
  };

  fs.writeFileSync(statusFile, JSON.stringify(status, null, 2));

  return status;
}

// If this file is run directly, perform check and log results
if (process.argv[1] === new URL(import.meta.url).pathname) {
  checkServices()
    .then((status) => console.log("Service status updated:", status))
    .catch((err) => console.error("Failed to check services:", err));
}

export default checkServices;
