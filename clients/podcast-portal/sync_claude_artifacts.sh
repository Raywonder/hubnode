#!/bin/bash

# Claude artifact URL (user can change this)
CLAUDE_URL="https://claude.ai/public/artifacts/00579f89-2f4e-4115-a56c-f9b091e22a31"

# Destination Git repo directory
DEST_DIR="/home/devinecr/apps/hubnode/clients/podcast-portal"

# Temp directory to hold download
TMP_DIR="/tmp/claude_artifacts_$(date +%s)"

mkdir -p "$TMP_DIR"
cd "$TMP_DIR" || exit 1

echo "[*] Downloading artifact from: $CLAUDE_URL"
FILENAME=$(curl -s -L -o /dev/null -w '%{url_effective}' "$CLAUDE_URL" | sed 's/.*\///')
curl -L "$CLAUDE_URL" -o "$FILENAME"

if [[ "$FILENAME" == *.zip ]]; then
  echo "[*] Unzipping artifact..."
  unzip -q "$FILENAME"
else
  echo "[*] Non-zip file, using as-is."
fi

echo "[*] Syncing to: $DEST_DIR"
rsync -av --progress . "$DEST_DIR/"

cd "$DEST_DIR" || exit 1

echo "[*] Git add/commit/push"
git add .
git commit -m "Synced Claude AI artifact on $(date)"
git push origin master


echo "[?] Done. All files synced and pushed."
