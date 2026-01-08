#!/bin/bash
echo "Restarting Softnode Media Player..."
sudo systemctl restart softnode-media-player
sudo systemctl status softnode-media-player --no-pager
