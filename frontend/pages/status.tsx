import React, { useEffect, useState } from "react";

interface ServiceStatus {
  name: string;
  status: string;
  error?: string;
  time: string;
}

interface SystemStatus {
  timestamp: string;
  system: {
    os: string;
    uptimeSeconds: number;
    memory: { totalBytes: number; freeBytes: number };
  };
  services: ServiceStatus[];
}

export default function Status() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/status")
      .then((res) => res.json())
      .then((data) => {
        setStatus(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading...</div>;
  if (!status) return <div>No status available</div>;

  return (
    <div style={{ padding: "1rem", fontFamily: "sans-serif" }}>
      <h1>System Status (updated at {new Date(status.timestamp).toLocaleTimeString()})</h1>
      <p>OS: {status.system.os}</p>
      <p>Uptime: {(status.system.uptimeSeconds / 3600).toFixed(2)} hours</p>
      <p>
        Memory: {(status.system.memory.freeBytes / 1024 / 1024).toFixed(0)}MB free of{" "}
        {(status.system.memory.totalBytes / 1024 / 1024).toFixed(0)}MB
      </p>

      <h2>Services</h2>
      <ul>
        {status.services.map((s) => (
          <li key={s.name} style={{ color: s.status === "OK" ? "green" : "red" }}>
            {s.name}: {s.status}
            {s.error && <em> — {s.error}</em>}
          </li>
        ))}
      </ul>
    </div>
  );
}
