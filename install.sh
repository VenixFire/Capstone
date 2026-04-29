#!/bin/bash

echo ---- VANDAL OPTICS INSTALLING DEPENDENCIES ----
USER=$(whoami)
ROOT=root

if [[$USER -eq $ROOT]]; then

    echo // Installing Necessary Python Packages
    #
    sudo apt install python3-pyvisa python3-zeroconf python3-psutil



    echo // Installing Necessary Packages
    #
    sudo apt install avahi-daemon nmcli



    # /etc/udev/rules.d
    RULE_FILE="/etc/udev/rules.d/ThorLabs.rules"
    echo // Adding rules for PyVisa Access
    if [ -f $RULE_FILE ]; then
        touch /etc/udev/rules.d/ThorLabs.rules
        echo \#USBTMC Instruments\n\# ThorLabs PM61\nSUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="1313", ATTRS{idProduct}=="80b4", GROUP="usbtmc", MODE="0660" > /etc/udev/rules.d/ThorLabs.rules
    else
        echo // Rule file already exists!
    fi


else
    echo // You need to run 'sudo install.sh'
fi
