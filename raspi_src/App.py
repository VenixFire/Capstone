"""
VandalOptics
Capstone Design Team 1

Description:
    Main app script, handles startup of logging
    and other methods

Authors:
    Jack Chambers

"""

"""
TODO:
- add snapping weight for points

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
    device = PowerMeter.PowerMeter() #cmdLogEnb=True)
    device.connect()
    
    # initialize device parameters
    device.setMeasurementUnit(PowerMeter.MODE_WATT)
    device.setWavelength(870)
    device.setMeasurementRange(2e-6)

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
        nPoints = int(input('Enter number of calibration points:'))
        calibration.create(device.getPowerReading, points=nPoints)
        calibration.load(Calibrations.DEFAULT_CAL_NAME)

    # reading cycle
    try:
        while True:
            val = device.getPowerReading()
            #result = calibration.read(val)

            # msg = ''
            # if result == 0.0:
            #     msg = 'Empty'
            # elif result == 1.0:
            #     msg = 'Full'

            print("@ Measurement:", val)
            # print("@ Output:", msg)

            time.sleep(1)

    except KeyboardInterrupt:
        device.disconnect()