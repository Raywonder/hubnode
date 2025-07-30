import { Router } from "express";
import checkServices from "../monitor";
import fs from "fs";
import path from "path";

const router = Router();
const statusFile = path.resolve(__dirname, "../../status.json");

// GET /api/status - return last known status JSON
router.get("/", (req, res) => {
  if (!fs.existsSync(statusFile)) {
    return res.status(404).json({ error: "Status file not found" });
  }
  const data = fs.readFileSync(statusFile, "utf-8");
  res.json(JSON.parse(data));
});

// POST /api/status/check - trigger a new status check and return result
router.post("/check", async (req, res) => {
  try {
    const status = await checkServices();
    res.json({ message: "Status updated", status });
  } catch (err) {
    res.status(500).json({ error: (err as Error).message });
  }
});

export default router;
