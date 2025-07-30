import { Router } from "express";
import {
  createApp,
  listApps,
  getApp,
  buildApp,
  pushApp,
  deleteApp,
} from "../controllers/app.controller";

const router = Router();

// Core RESTful endpoints
router.post("/create", createApp);
router.get("/list", listApps);
router.get("/:id", getApp);
router.post("/:id/build", buildApp);
router.post("/:id/push", pushApp);
router.delete("/:id", deleteApp);

// Legacy/simple dev test endpoint
router.post("/generate", (req, res) => {
  const { appName } = req.body;
  console.log(`[+] Received app generation request for: ${appName}`);
  return res.status(200).json({ message: `App ${appName} generation requested.` });
});

export default router;
