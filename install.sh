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

# /etc/udev/rules.d/...
RULE_FILE="/etc/udev/rules.d/ThorLabs.rules"
AP_CONF_FILE="/etc/NetworkManager/system-connections/AccessPoint.nmconnection"

if [[ "$USER" == "$ROOT" ]]; then

    # Install necessary python packages
    echo
    echo "----// Installing Necessary Python Packages"
    sudo apt install python3-pyvisa python3-zeroconf python3-psutil


    # Install necessary linux packages
    echo
    echo "----// Installing Necessary Packages"
    sudo apt install avahi-daemon network-manager


    # Define ruleset for pyvisa access to peripherals
    echo
    echo "----// Adding rules for PyVisa Access"
    if [ -f "$RULE_FILE" ]; then
        echo "--// Rule file already exists, no overwriting"
    else
        touch /etc/udev/rules.d/ThorLabs.rules
        echo -e "\#USBTMC Instruments\n\# ThorLabs PM61\nSUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="1313", ATTRS{idProduct}=="80b4", GROUP="usbtmc", MODE="0660"" > /etc/udev/rules.d/ThorLabs.rules
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
        sudo nmcli conn up $AP_ID
    fi

else
    echo "--// You need to run as sudo -- 'sudo install.sh'"
fi
