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