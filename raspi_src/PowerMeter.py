"""

Jack Chambers
Senior Design 1

PM61 representation class
Includes reading from calibration files

Windows Dependencies:
    pyvisa
    pyvisa-py
    pyusb
    libusb_package
    warnings
    csv
    
    PM61 USB Drivers
"""

#Import the PyVISA library to Python.
import pyvisa
import warnings
import sys
import time
import csv
from pathlib import Path


# mute warnings
warnings.filterwarnings("ignore")


# pm61 class
class PowerMeter:

    # Instantiate
    def __init__(self, calDir="./cal", isSimulated=False):

        # simulation
        if isSimulated:
            self._rm = pyvisa.ResourceManager('PM61_SIM.yaml@sim')
        else:
            self._rm = pyvisa.ResourceManager()

        self._device = None
        self._calDirectory = calDir



    # tostring definition
    def __str__(self):
        return "PM61"
    


    # Open a session
    def connect(self):
        print("# ATTEMPT TO CONNECT")
        
        # generate the resourcelist
        resourceList = self._rm.list_resources()
        print("# RESOURCES", resourceList, "\n")
        
        # ensure there is the one device connected
        if len(resourceList) > 0:
            deviceId = resourceList[0]
        else:
            print("! NO DEVICES CONNECTED")
            return

        # Connect to pm61 (should be only available device)
        self._device = self._rm.open_resource(deviceId)
        print("# CONNECTION OPENED")


        # print the device information
        # PM61A, 250219304 supposedly
        self._device.write('*IDN?')
        self._device.read('\n')
        print("# DEVICE", self._device.query("SYST:SENS:IDN?"))
        
    

    # Setup the PM61 state
    def setupSensors(self):
        if self._device is None:
            print("! DEVICE NOT CONNECTED, CANNOT SETUP SENSORS")
            return

        #turn on auto-ranging
        self._device.write("SENS:RANGE:AUTO ON")
        
        #set wavelength setting, so the correct calibration point is used
        self._device.write("SENS:CORR:WAV 870")
        
        #set units to dbm
        self._device.write("SENS:POW:UNIT DBM")



    # Disconnect from the PM61
    def disconnect(self):
        print("# DISCONNECTING")
        #Close device in any case
        if self._device is not None:
            try:
                self._device.close()
            except Exception:
                pass

        #Close resource manager in any case
        if self._rm is not None:
            try:
                self._rm.close()
            except Exception:
                pass



    # Read Device Charge
    def readCharge(self):
        if self._device is None:
            return
        
        batteryLevel = self._device.query("SYST:BATT:SOC?")
        print("# CURRENT CHARGE", batteryLevel)

    

    def takeReading(self):
        if self._device is None:
            print("! CANNOT TAKE READING, DEVICE NOT CONNECTED")
            return

        # send a beep to the deviceId
        self._device.write("SYST:BEEP")

        # perform reading
        dbm = self._device.query("MEAS:POW?")
        print("# DBM READING", dbm)

        # wait
        time.sleep(1)



    # Read a cal from CSV
    # TODO: move to another place, this is just temp here for now
    # 
    def read_calibration_csv(self, metric : str):
        
        fileName = f"CAL_{metric}.csv"
        filePath = Path(self._calDirectory) / fileName

        if not filePath.exists():
            raise FileNotFoundError(f"Calibration file not found: {filePath}")

        data = []

        with open(filePath, newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)

            # Validate expected columns
            expectedFields = {"Reading", "Result", "Unit"}
            
            if not expectedFields.issubset(reader.fieldnames):
                raise ValueError(
                    f"CSV must contain columns {expectedFields}, "
                    f"found {reader.fieldnames}"
                )

            for row in reader:
                data.append({
                    "Reading": float(row["Reading"]),
                    "Result": float(row["Result"]),
                    "Unit": row["Unit"]
                })

        return data



# Example if this is run as main
if __name__ == "__main__":
    # define the device
    device = PowerMeter()
    
    # connect to pm61
    device.connect()

    # setup sensors for readings
    device.setupSensors()

    # take a reading
    device.takeReading()

    # disconnect the pm61
    device.disconnect()