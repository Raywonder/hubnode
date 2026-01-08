#!/bin/bash
echo "Starting Softnode Media Player..."
sudo systemctl start softnode-media-player
sudo systemctl status softnode-media-player --no-pager
