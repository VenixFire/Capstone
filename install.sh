#!/bin/bash

# VandalOptics
# Jack Chambers
# install script wrapper -- sends the output to a log

# Testfor logs folder

if [ -d "logs" ]; then
    echo -e "\r"
else
    mkdir logs
fi

LOG_NAME="install_log_$(date +%F).txt"
touch logs/$LOG_NAME

scripts/install.sh >> logs/$LOG_NAME