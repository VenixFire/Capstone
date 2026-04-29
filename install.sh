#!/bin/bash

# VandalOptics
# install.sh
# Contributors: Jack Chambers
#
# Install necessary dependencies and such for the program

echo ---- VANDAL OPTICS INSTALLING DEPENDENCIES ----
USER=$(whoami)
ROOT=root

AP_ID="AccessPoint"
AP_NAME="VandalOptics"
AP_PWD="GoVandals!"

VENDOR_ID=1313
PRODUCT_ID=80b4



# /etc/udev/rules.d/...
RULE_FILE="/etc/udev/rules.d/ThorLabs.rules"
AP_CONF_FILE="/etc/NetworkManager/system-connections/AccessPoint.nmconnection"
SERVICE_FILE="/etc/systemd/system/vandaloptics-logger.service"


## User if
if [[ "$USER" == "$ROOT" ]]; then

# Install necessary python packages
echo
echo "----// Installing Necessary Python Packages"
sudo apt install python3-pyvisa python3-zeroconf python3-psutil python3-numpy


# Install necessary linux packages
echo
echo "----// Installing Necessary Packages"
sudo apt install avahi-daemon network-managers


# Define ruleset for pyvisa access to peripherals
echo
echo "----// Adding rules for PyVisa Access"
if [ -f "$RULE_FILE" ]; then
echo "--// Rule file already exists, no overwriting"
else
touch /etc/udev/rules.d/ThorLabs.rules
echo -e "
# USBTMC Instruments List

# ThorLabs PM61
SUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="$VENDOR_ID", ATTRS{idProduct}=="$PRODUCT_ID", GROUP="usbtmc", MODE="0660"
" > /etc/udev/rules.d/ThorLabs.rules
echo "--// Successfully wrote rules"
fi


# Check for existing network configuration
echo 
echo "----// Establishing AccessPoint"
if nmcli conn | grep -q "$AP_ID"; then
echo "--// Access point config file already exists."
else
echo "--// Creating new AccessPoint connection"
sudo nmcli dev wifi hotspot ifname wlan0 ssid $AP_NAME password $AP_PWD con-name $AP_ID
fi

if [ $1 == '--ignore-ap' ]; then
echo "--// Ignoring AccessPoint"
else
echo "--// Brining AccessPoint up"
sudo nmcli conn up $AP_ID
fi


# Define a new service for the logger to run off
echo
echo "----// Creating new vandaloptics-logger.service"
if [ -f $SERVICE_FILE ]; then
echo "--// Service already exists!"
else
echo "--// Service doesn't exist, creating service"
sudo touch $SERVICE_FILE

echo "
[Unit]
Description=VandalOptics Logger Service
After=network.target
StartLimitIntervalSec=0
[Service]
Type=simple
Restart=always
RestartSec=1
User=logger
ExecStart=/home/logger/Capstone/launch.sh

[Install]
WantedBy=multi-user.target
" > $SERVICE_FILE
fi



## User else
else
echo "--// You need to run as sudo -- 'sudo ./install.sh'"
fi
