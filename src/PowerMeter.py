"""

VandalOptics
Capstone Design Teams 1

Description:
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

Authors:
    Jack Chambers

"""

#Import the PyVISA library to Python.
import pyvisa
import warnings
import time
import scpi_util


# Constants
MAX_WAVELENGTH = 1500
MIN_WAVELENGTH = 500

MODE_DBM = "DBM"
MODE_WATT = "W"

# unique device string
# should be more secret maybe, IDGAF!
USB_DEVICE_STRING = "USB0::4883::32948::250219304::0::INSTR"

# mute warnings
warnings.filterwarnings("ignore")

# pm61 class
class PowerMeter:

    # Instantiate

    """
        Private Methods
    """

    # Constructor
    def __init__(self, logger=None, deviceId=None, isSimulated=False, cmdLogEnb=False):

        self._deviceId = deviceId
        self._device = None
        self._unit = None
        self._range = None
        self._cmdLogEnb = cmdLogEnb
        self._logger = logger

        # simulation
        if isSimulated:
            self._rm = pyvisa.ResourceManager('PM61_SIM.yaml@sim')
        else:
            self._rm = pyvisa.ResourceManager()


    def __str__(self):
        return "PM61"
    

    def __assertConnection(self) -> bool:
        assert self._device != None, "PowerMeter: No Device Connected"
        

    def __write(self, command : str) -> None:
        self.__assertConnection()
        if self._cmdLogEnb:
            self.__log(f"$ w: {command}")
        self._device.write(command)


    def __query(self, command : str) -> any:
        self.__assertConnection()
        if self._cmdLogEnb:
            self.__log(f"$ q {command}")
        return self._device.query(command)
    

    def __log(self, stringToPrint):
        if self._logger != None:
            self._logger.log(f"[INFO] {stringToPrint}")
        else:
            print(stringToPrint)


    """
        Public Methods
    """
    def connect(self, logger=None) -> None:
        self.__log("ATTEMPTING TO CONNECT")
        # generate the resourcelist
        resourceList = self._rm.list_resources()
        self.__log(f"AVAILABLE RESOURCES: {resourceList}")

        # select a device from the list
        if self._deviceId == None:
            
            # ensure there is the one device connected
            if len(resourceList) > 0:
                deviceId = resourceList[0]
            else:
                self.__log("! NO DEVICES CONNECTED")
                return
            
            self._deviceId = deviceId

        try:
            self._device = self._rm.open_resource(self._deviceId)
            self.__log(f"CONNECTION OPENED WITH ID: {self._deviceId}")

            # print the device information
            # PM61A, 250219304 supposedly
            # self._device.write('*IDN?')
            # self._device.read('\n')
            self.__log(f"DEVICE {self.__query("SYST:SENS:IDN?")}")
        except:
            self.__log("FAILED TO CONNECT TO DEVICE! | RETRYING IN 3S")
            time.sleep(3)

    
    def disconnect(self) -> None:
        self.__log(f"DISCONNECTING FROM ID: {self._deviceId}")
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

        self._device = None

    
    """None -> AutoRange; range is in W"""
    def setMeasurementRange(self, range : None | float) -> None:
        self.__assertConnection()
        if range is None:
            self.__write(f"SENS:POW:RANG:AUTO ON")
        else:
            self.__write(f"SENS:POW:RANG {range}")


    """Wavelength in nm"""
    def setWavelength(self, lambda_nm : int):
        self.__assertConnection()
        assert(type(lambda_nm) == int)
        self.__write(f"SENS:CORR:WAV {lambda_nm}")


    """DBM or W"""
    def setMeasurementUnit(self, unitName : str) -> None:
        self.__assertConnection()
        assert((unitName == "DBM") or (unitName == "W"))
        self._unit = unitName
        self.__write(f"SENS:POW:UNIT {unitName}")


    """Set reference for delta readings"""
    def setDeltaReference(self, reference=0):
        self.__assertConnection()
        self.__write(f"SENS:POW:REF {reference}")


    """Enable Delta Readings"""
    def setDeltaEnabled(self, isEnabled=True):
        self.__assertConnection()
        deltaFlagBit = scpi_util.BOOL_ONOFF(isEnabled)
        self.__write(f"SENS:POW:REF:STAT {deltaFlagBit}")


    """AutoRange, 870nm, DBM"""
    def setDefaultOptions(self) -> None:
        self.__assertConnection()
        self.setMeasurementRange(None)
        self.setWavelength(870)
        self.setMeasurementUnit("DBM")


    """Return float for charge percent"""
    def getBatteryCharge(self) -> float:
        self.__assertConnection()
        return self.__query("SYST:BATT:SOC?")


    """Returns the power measurement"""
    """Provides higher resolution than visible on the PM60 itself"""
    def getPowerReading(self) -> float:
        self.__assertConnection()
        assert self._unit != None, "PowerMeter: Undeclared Measurement Unit"
        resultString = self.__query("MEAS:POW?")
        resultFloat = float(resultString)
        return resultFloat
    

    """System beep"""
    def beep(self):
        self.__assertConnection()
        self._device.write("SYST:BEEP")


    def isConnected(self) -> bool:
        return (self._device != None)
    
    def rawQuery(self, cmd):
        return self.__query(cmd)



"""
    Example Behavior
"""
if __name__ == "__main__":
    device = PowerMeter(deviceId=USB_DEVICE_STRING, cmdLogEnb=True)
    device.connect()
    
    device.setMeasurementUnit("W")
    device.setWavelength(870)
    device.setMeasurementRange(200e-6)

    try:
        while True:
            val = device.getPowerReading()
            #val = device.rawQuery("MEAS:POW?")
            print("# MEASUREMENT:", val)
            time.sleep(1.5)

    except KeyboardInterrupt:
        device.disconnect()
