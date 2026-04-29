#!/bin/bash
# started by vandaloptics-logger.service
# runs headless volume sensor and logs to device data

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/DeviceData/Logs"

mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/VolumeSensorHeadless_$(date +%Y%m%d_%H%M%S).log"

python3 "$SCRIPT_DIR/src/VolumeSensorHeadless.py" >> "$LOG_FILE" 2>&1