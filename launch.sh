#!/bin/bash

# VandalOptics
# launch.sh
# Contributors: Jack Chambers
# 
# Launches necessary components / features for operation

## Title
echo "---- VANDAL OPTICS LAUNCH SCRIPT ----"

## Start avahi-daemon for dns resolution
echo -e "\n--// Launching avahi-daemon"

## Enable Access Point with network-manager
echo -e "\n--// Enabling Access Point"

FILE="~/created_by_service"
touch $FILE
$(whoami) > $FILE