"""
Calibrations Manager

Writing to and reading from the calibration files


TODO:
 - refine file selection procedure
 - add in compatibility with ContentServe

"""

import json
import numpy as np

DEFAULT_CAL_NAME = "DefaultCalibration"

class Calibration:
    def __init__(self, fileName=DEFAULT_CAL_NAME, autoSetCalibration=False):
        # Private Values
        self._activeCalibrationName = fileName
        self._polyFunc = None

        # Autoload calibration
        if autoSetCalibration:
            self.setCalibration(self.activeCalibrationName)



    def load(self, name):
        # define filename
        fName = f"{name}.json"
        x = []
        y = []

        # Attempt to load calibration from a file
        try:
            with open(fName, "r") as fptr:
                samplesLoaded = json.load(fptr)
                calibrationArray = np.array(samplesLoaded).astype(np.float64)

        except FileNotFoundError:
            print(f"! No such calibration exists '{fName}'")
            return

        # define points along curve
        for pair in calibrationArray:
            x.append(pair[0])
            y.append(pair[1])

        # generate a regression model polynomial
        # redefine the read method
        # https://stackoverflow.com/questions/6148207/linear-regression-with-matplotlib-numpy
        polynomialCoefficients = np.polyfit(x,y,1)
        self._polyFunc = np.poly1d(polynomialCoefficients)



    """Check whether a calibration exists in the filesystem"""
    def doesCalibrationExist(self, calibrationName=None) -> bool:
        fName = ""
        if calibrationName:
            fName = f"{calibrationName}.json"
        else:
            fName = f"{DEFAULT_CAL_NAME}.json"

        try:
            with open(fName, "r") as fptr:
                fptr.close()
                return True
        except:
            return False



    def create(self, readingCallback, name=None, samples=50, points=2):
        # select a filename
        # TODO: refine file selection procedure
        fName = ""
        if name:
            fName = f"{name}.json"
        else:
            fName = f"{DEFAULT_CAL_NAME}.json"

        sampleEntries = []

        # generate results for each output point
        for n_o in range(points):

            # define the output value
            print(f"Output for Position {n_o}?")
            mapping = int(input())

            # generate samples
            print(f"Press Enter to Calibrate for {mapping}:")
            input()
            for n_s in range(samples):
                reading = readingCallback()
                sampleEntries.append([reading, mapping])

        # sort the samples by mapping, low to high
        sampleEntries.sort(key=lambda tup : tup[1])

        # save sample entries to json
        with open(fName, "w") as fptr:
            json.dump(sampleEntries, fptr)



    def read(self, inputValue) -> float | None:
        if self._polyFunc == None:
            print("! No calibration set, please set one before reading")
            return None
        else:
            return self._polyFunc(inputValue)



    def getFileName(self):
        return self._activeCalibrationName