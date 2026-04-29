#!/bin/bash

echo ---- VANDAL OPTICS INSTALLING DEPENDENCIES ----
USER=$(whoami)
ROOT=root

if [[ "$USER" == "$ROOT" ]]; then

    echo "--// Installing Necessary Python Packages"
    #
    sudo apt install python3-pyvisa python3-zeroconf python3-psutil



    echo "--// Installing Necessary Packages"
    #
    sudo apt install avahi-daemon network-manager



    # /etc/udev/rules.d
    RULE_FILE="/etc/udev/rules.d/ThorLabs.rules"
    echo "--// Adding rules for PyVisa Access"
    if [ -f "$RULE_FILE" ]; then
        echo "--// Rule file already exists, no overwriting"
    else
        touch /etc/udev/rules.d/ThorLabs.rules
        echo -e "\#USBTMC Instruments\n\# ThorLabs PM61\nSUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="1313", ATTRS{idProduct}=="80b4", GROUP="usbtmc", MODE="0660"" > /etc/udev/rules.d/ThorLabs.rules
        echo "--// Successfully wrote rules"
    fi

else
    echo "--// You need to run as sudo -- 'sudo install.sh'"
fi
