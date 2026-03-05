"""
Calibrations Manager

Writing to and reading from the calibration files


TODO:
 - refine file selection procedure
 - add in compatibility with ContentServe

"""

import json
import numpy as np

class Calibration:
    def __init__(self, defaultName="DefaultCalibration"):
        self.defaultCalibrationName = f"{defaultName}.json"
        self.activeCalibrationName = self.defaultCalibrationName
        pass


    def set(self, name):
        # define filename
        fName = f"{name}.json"
        calibrationArray = np.array(samplesLoaded).astype(np.float64)
        x = []
        y = []

        # Load calibration from a file
        with open(fName, "r") as fptr:
            samplesLoaded = json.load(fptr)

        # define points along curve
        for pair in calibrationArray:
            x.append(pair[0])
            y.append(pair[1])

        # generate a regression model polynomial
        # redefine the read method
        # https://stackoverflow.com/questions/6148207/linear-regression-with-matplotlib-numpy
        polynomialCoefficients = np.polyfit(x,y,1)
        self.read = np.poly1d(polynomialCoefficients)


    def hasCalibration(self) -> bool:
        fName = ""

        if self.activeCalibrationName:
            fName = self.activeCalibrationName
        else:
            fName = self.defaultCalibrationName

        fileStr = f"{fName}.json"

        try:
            with open(fileStr, "r") as fptr:
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
            fName = self.defaultCalibrationName

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


    def read(self, inputValue):
        return None
    

    def getDefaultCalibrationName(self):
        return self.defaultCalibrationName