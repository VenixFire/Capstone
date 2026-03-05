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


def callback():
    return 0


if __name__ == "__main__":
    # Define top-level services
    device = PowerMeter.PowerMeter(cmdLogEnb=True)
    calibration = Calibrations.Calibration()

    # # establish connection
    # device.connect()
    
    # # initialize device parameters
    # device.setMeasurementUnit("W")
    # device.setWavelength(870)
    # device.setMeasurementRange(200e-6)

    # check for a calibration
    calName = calibration.getDefaultCalibrationName()
    hasCal = calibration.hasCalibration()
    print(hasCal)
    if hasCal != True:
        calibration.create(calName, callback)
    else:
        

    # try:
    #     while True:
    #         val = device.getPowerReading()
    #         print("# MEASUREMENT:", val)
    #         time.sleep(0.5)

    # except KeyboardInterrupt:
    #     device.disconnect()