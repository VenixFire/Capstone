"""
Docstring for raspi_src.main

PM61 reading

Windows Dependencies:
    pyvisa
    pyvisa-py
    pyusb
    libusb_package
    warnings
    sys
    tkinter
    csv
    
    PM61 USB Drivers

"""

from PowerMeter import *
from Calibration import *

# create calibrations
calVolume = Calibration("volume")

# create the device and connect
device = PowerMeter()
device.connect()

if device.isConnected():

    # prep sensors for readings
    device.setupSensors()

    # take reading
    read = device.takeReading()
    result = calVolume.get(read)

# disconnect the device when done
device.disconnect()