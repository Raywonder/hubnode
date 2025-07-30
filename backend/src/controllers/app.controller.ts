import { Request, Response } from "express";
import fs from "fs";
import path from "path";

const appsRoot = "/home/devinecr/apps/hubnode/clients";

function getAppPath(id: string) {
  return path.join(appsRoot, id);
}

function getMetaFile(id: string) {
  return path.join(getAppPath(id), "meta.json");
}

function readMeta(id: string) {
  const metaFile = getMetaFile(id);
  if (!fs.existsSync(metaFile)) return null;
  return JSON.parse(fs.readFileSync(metaFile, "utf-8"));
}

function writeMeta(id: string, data: any) {
  const metaFile = getMetaFile(id);
  fs.writeFileSync(metaFile, JSON.stringify(data, null, 2));
}

export const createApp = (req: Request, res: Response) => {
  const { name, user } = req.body;
  const appDir = getAppPath(name);

  if (!name || !user) return res.status(400).json({ error: "Missing name or user" });
  if (fs.existsSync(appDir)) return res.status(409).json({ error: "App already exists" });

  fs.mkdirSync(appDir, { recursive: true });
  fs.mkdirSync(path.join(appDir, "versions"), { recursive: true });

  const meta = {
    name,
    user,
    createdAt: new Date().toISOString(),
    versions: [],
  };

  writeMeta(name, meta);
  return res.status(201).json({ message: "App created", path: appDir });
};

export const listApps = (req: Request, res: Response) => {
  const apps = fs.readdirSync(appsRoot).filter(f =>
    fs.statSync(path.join(appsRoot, f)).isDirectory()
  );
  return res.json({ apps });
};

export const getApp = (req: Request, res: Response) => {
  const id = req.params.id;
  const meta = readMeta(id);
  if (!meta) return res.status(404).json({ error: "App not found" });
  return res.json({ app: meta });
};

export const buildApp = (req: Request, res: Response) => {
  const id = req.params.id;
  const { versionType = "dev" } = req.body; // dev or prod

  const appDir = getAppPath(id);
  if (!fs.existsSync(appDir)) return res.status(404).json({ error: "App not found" });

  // Simulate a build process
  const versionName = `${versionType}-${Date.now()}`;
  const versionDir = path.join(appDir, "versions", versionName);
  fs.mkdirSync(versionDir, { recursive: true });

  // Simulate artifact creation
  const artifactPath = path.join(versionDir, `${id}-${versionType}.zip`);
  fs.writeFileSync(artifactPath, `Build content for ${id} [${versionType}]`);

  // Update metadata
  const meta = readMeta(id);
  meta.versions.push({ version: versionName, type: versionType, createdAt: new Date().toISOString() });
  writeMeta(id, meta);

  return res.json({ message: `Build completed`, version: versionName, artifact: artifactPath });
};

export const pushApp = (req: Request, res: Response) => {
  const id = req.params.id;
  const { version } = req.body;

  const appDir = getAppPath(id);
  const versionDir = path.join(appDir, "versions", version || "");
  if (!fs.existsSync(versionDir)) return res.status(404).json({ error: "Version not found" });

  const deployDir = path.join(appDir, "live");
  fs.rmSync(deployDir, { recursive: true, force: true });
  fs.mkdirSync(deployDir, { recursive: true });

  // Copy placeholder
  fs.copyFileSync(
    path.join(versionDir, `${id}-dev.zip`), // fallback for dev
    path.join(deployDir, `${id}.zip`)
  );

  const meta = readMeta(id);
  meta.lastPushed = {
    version,
    pushedAt: new Date().toISOString(),
  };
  writeMeta(id, meta);

  return res.json({ message: `Pushed version ${version} to live`, path: deployDir });
};

export const deleteApp = (req: Request, res: Response) => {
  const id = req.params.id;
  const appDir = getAppPath(id);

  if (!fs.existsSync(appDir)) return res.status(404).json({ error: "App not found" });

  fs.rmSync(appDir, { recursive: true, force: true });
  return res.json({ message: `App ${id} deleted` });
};
