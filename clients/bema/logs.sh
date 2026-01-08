#!/bin/bash
echo "Viewing Softnode Media Player logs..."
echo "Press Ctrl+C to exit"
echo "=========================="
sudo journalctl -u softnode-media-player -f
