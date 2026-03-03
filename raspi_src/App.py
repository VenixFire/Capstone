"""
VandalOptics
Capstone Design Team 1

Description:
    Main app script, handles startup of logging
    and other methods

Authors:
    Jack Chambers

"""

# General Packages
import time

# System Packages
import PowerMeter
import ActionLog
import Calibrations
import ContentServe
import ResultLog


if __name__ == "__main__":
    device = PowerMeter.PowerMeter(cmdLogEnb=True)
    device.connect()
    
    device.setMeasurementUnit("W")
    device.setWavelength(870)
    device.setMeasurementRange(200e-6)

    try:
        while True:
            val = device.getPowerReading()
            print("# MEASUREMENT:", val)
            time.sleep(0.5)

    except KeyboardInterrupt:
        device.disconnect()