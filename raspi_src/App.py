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
import Calibrations
import ContentServe
import ResultLog


if __name__ == "__main__":
    # get the device loaded
    device = PowerMeter.PowerMeter(cmdLogEnb=True)
    device.connect()
    
    # initialize device parameters
    device.setMeasurementUnit("W")
    device.setWavelength(870)
    device.setMeasurementRange(200e-6)

    # prepare calibration manager
    calibration = Calibrations.Calibration()

    # check for an existing calibration
    if calibration.doesCalibrationExist(Calibrations.DEFAULT_CAL_NAME):
        # load the calibration
        calName = calibration.getFileName()
        calibration.load(calName)
        print(f"# Calibration loaded {calName}")

    # generate a new calibration
    else:
        print(f"! No calibration present, creating a new one.")
        calibration.create(device.getPowerReading)
        calibration.load(Calibrations.DEFAULT_CAL_NAME)

    # reading cycle
    try:
        while True:
            val = device.getPowerReading()
            result = calibration.read(val)
            print("@ Measurement:", val)
            print("@ Output:", result)
            time.sleep(1.5)

    except KeyboardInterrupt:
        device.disconnect()