#!/bin/bash

# Simple git commit & push helper for general users
# Usage: ./git-push-helper.sh "Commit message here"

if [ -z "$1" ]; then
  echo "Error: Commit message is required."
  echo "Usage: $0 \"Your commit message\""
  exit 1
fi

read -p "You are about to commit and push ALL changes to the current branch. Continue? (y/n) " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "Aborted by user."
  exit 0
fi

current_branch=$(git rev-parse --abbrev-ref HEAD)

echo "[*] Adding all changes..."
git add .

echo "[*] Committing changes..."
git commit -m "$1"

echo "[*] Pushing to branch '$current_branch'..."
git push origin "$current_branch"

echo "[+] Done."
