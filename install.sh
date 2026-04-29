#!/bin/bash

# VandalOptics
# Jack Chambers
# install script wrapper -- sends the output to a log

# Testfor logs folder

if [ -d "logs" ]; then
    # do nothing
else
    mkdir logs
fi

scripts/install.sh >> /logs/install_log_$(date +%F).txt