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
import numpy as np
import json
import time

# create calibrations
# create the device and connect
device = pm.PowerMeter()
device.connect()


# ensure connection
# prep device for readings
device.setMeasurementUnit("W")
device.setWavelength(870)
device.setMeasurementRange(200e-6)


# Load calibration from a file
with open("cal.json", "r") as fptr:
    samplesLoaded = json.load(fptr)

calibration = np.array(samplesLoaded).astype(np.float64)
x = []
y = []

for pair in calibration:
    x.append(pair[1])
    y.append(pair[0])

# https://stackoverflow.com/questions/6148207/linear-regression-with-matplotlib-numpy
polyCoef = np.polyfit(x,y,1)
poly1d_func = np.poly1d(polyCoef)


# Connect and print results
try:
    while True:
        val = device.getPowerReading()
        alpha = poly1d_func(val)
        print("Result:",alpha)
        time.sleep(0.1)

except KeyboardInterrupt:
    device.disconnect()
    
    

