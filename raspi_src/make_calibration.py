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

# create calibrations
# newCalVolume = cal.Calibration("volume", "calibrations", createNewCal=True, writeEnabled=True)

# create the device and connect
device = pm.PowerMeter()
device.connect()

# ensure connection
# prep device for readings
device.setMeasurementUnit("W")
device.setWavelength(870)
device.setMeasurementRange(200e-6)

print("How Many Outputs to Map?")
nOutputs = int(input())

print("How many samples per ouput?")
nSamples = int(input())

sampleEntries = []

for n in range(nOutputs):
    print(f"Mapping for Output {n}?")
    mapping = int(input())

    # generate samples
    sampleResult = np.zeros([nSamples]).astype(np.float64)
    for sIdx in range(nSamples):
        sampleResult[sIdx] = device.getPowerReading()

    # output sample results
    avg = np.average(sampleResult)
    sampleEntries.append([mapping, avg])

sampleEntries.sort(key=lambda tup : tup[0])

with open("cal.json", "w") as fptr:
    json.dump(sampleEntries, fptr)

