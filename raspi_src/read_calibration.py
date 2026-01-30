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

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolate on the scale given by a to b, using t as the point on that scale."""
    return (1 - t) * a + t * b

def alpha(x, min, max):
    return (x-min) / (x-max)


def map(calibration, value):
    bounds = [0.0, 0.0]
    values = [0.0, 0.0]
    fval = float(value)

    # get new range for mapping
    for entry in calibration:
        output = entry[0]
        reading = entry[1]

        if reading > bounds[0]:
            bounds[0] = reading
            values[0] = output

        if reading < bounds[1]:
            bounds[1] = reading
            values[1] = output

    a = alpha(fval, values[0], values[1])
    return lerp(a, bounds[0], bounds[1])
    


# ensure connection
# prep device for readings
device.setMeasurementUnit("W")
device.setWavelength(870)
device.setMeasurementRange(200e-6)

with open("cal.json", "r") as fptr:
    samplesLoaded = json.load(fptr)

calibration = np.array(samplesLoaded).astype(np.float64)

try:
    while True:
        val = device.getPowerReading()
        print(map(calibration, val))
        time.sleep(0.1)
        
        

except KeyboardInterrupt:
    device.disconnect()
    
    

