#!/bin/bash
mkdir -p ~/.ssh
ssh-keygen -t ed25519 -f ~/.ssh/gitrepo -C "hubnode" -N ""
