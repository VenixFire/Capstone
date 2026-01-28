import PowerMeter as pm
import numpy as np

storedValues = []

pm60 = pm.PowerMeter()

with open("readings.csv", "a") as csvFileBase:
    pm60.connect()
    pm60.defaultSensorSetup()

    try:
        while True:
            # take a reading
            powerFloat = pm60.queryPowerMeasurement()
            csvFileBase.write(f",{powerFloat}")

    except KeyboardInterrupt:     
        # disconnect the pm61
        csvFileBase.close()
        pm60.disconnect()