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
import time
import scpi_util


# Constants
MAX_WAVELENGTH = 1500
MIN_WAVELENGTH = 500


# mute warnings
warnings.filterwarnings("ignore")


# pm61 class
class PowerMeter:

    # Instantiate

    """
        Private Methods
    """

    # Constructor
    def __init__(self, isSimulated=False, cmdLogEnb=False):
        self._device = None
        self._unit = None
        self._range = None
        self._cmdLogEnb = cmdLogEnb

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
            print("$ w: ", command)
        self._device.write(command)


    def __query(self, command : str) -> any:
        self.__assertConnection()
        if self._cmdLogEnb:
            print("$ q:", command)
        return self._device.query(command)


    """
        Public Methods
    """
    def connect(self) -> None:
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
        print("# DEVICE", self.__query("SYST:SENS:IDN?"))

    
    def disconnect(self) -> None:
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
        self.setAutoRanging(True)
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
        return self.__query("MEAS:POW?")
    

    """System beep"""
    def beep(self):
        self.__assertConnection()
        self._device.write("SYST:BEEP")


    def isConnected(self) -> bool:
        return (self._device != None)
    

    # def printQuery(self, cmd) -> None:
    #     print(self.__query(cmd))



"""
    Example Behavior
"""
if __name__ == "__main__":
    device = PowerMeter(cmdLogEnb=True)
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
