#!/bin/bash
# For vandaloptics-webserve.service
# starts webserve and logs to devicedata/logs

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/DeviceData/Logs"

mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/WebContentServe_$(date +%Y%m%d_%H%M%S).log"

python3 "$SCRIPT_DIR/src/WebContentServe.py" >> "$LOG_FILE" 2>&1