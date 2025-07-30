#!/bin/bash
echo "[*] Adding all changes..."
git add .
git commit -m "$1"
git push origin main
