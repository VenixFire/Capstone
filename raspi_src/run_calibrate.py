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


Linux Dependencies:


"""

import PowerMeter as pm
import Calibration

# create calibrations
calVolume = Calibration("volume")

# create the device and connect
device = pm.PowerMeter()
device.connect()

if device.isConnected():
    # prep device for readings
    device.setMeasurementUnit("W")
    device.setWavelength(870)
    device.setMeasurementRange(200e-6)

    # take reading
    read = device.takeReading()
    result = calVolume.get(read)

# disconnect the device when done
device.disconnect()