"""
Calibrations Manager

Writing to and reading from the calibration files

TODO:
 - refine file selection procedure
 - add in compatibility with ContentServe
"""

import json
import numpy as np
import time

DEFAULT_CAL_NAME = "DefaultCalibration"
CALIBRATION_SAMPLE_TIME = 60  # 1 minute


class Calibration:
    def __init__(self, fileName=DEFAULT_CAL_NAME, autoSetCalibration=False):
        # Private Values
        self._activeCalibrationName = fileName
        self._polyFunc = None  # (kept for compatibility, unused now)
        self._points = None    # raw calibration point cloud

        # Autoload calibration
        if autoSetCalibration:
            self.load(self._activeCalibrationName)


    def load(self, name):
        # define filename
        fName = f"{name}.json"

        try:
            with open(fName, "r") as fptr:
                samplesLoaded = json.load(fptr)
                calibrationArray = np.array(samplesLoaded).astype(np.float64)

        except FileNotFoundError:
            print(f"! No such calibration exists '{fName}'")
            return

        # store raw points (reading, mapping)
        self._points = calibrationArray
        self._activeCalibrationName = name


    """Check whether a calibration exists in the filesystem"""
    def doesCalibrationExist(self, calibrationName=None) -> bool:
        fName = f"{calibrationName or DEFAULT_CAL_NAME}.json"

        try:
            with open(fName, "r"):
                return True
        except FileNotFoundError:
            return False


    def create(self, readingCallback, name=None, samples=10, points=2):
        # select a filename
        fName = f"{name or DEFAULT_CAL_NAME}.json"

        sampleEntries = []
        timePerReading = CALIBRATION_SAMPLE_TIME / samples

        # generate results for each output point
        for n_o in range(points):

            # define the output value
            print(f"Output for Position {n_o+1}/{points}?")
            mapping = float(input())

            # generate samples
            print(f"Press Enter to Begin Calibration for Position {n_o+1}/{points}:")
            input()

            for n_s in range(samples):
                reading = readingCallback()
                sampleEntries.append([reading, mapping])

                print(f"Taking Reading {n_s + 1} / {samples} for Position {n_o}")
                time.sleep(timePerReading)

        # sort the samples by mapping (low → high)
        sampleEntries.sort(key=lambda tup: tup[1])

        # save sample entries to json
        with open(fName, "w") as fptr:
            json.dump(sampleEntries, fptr)


    def read(self, inputValue) -> float | None:
        if self._points is None or len(self._points) == 0:
            print("! No calibration set, please set one before reading")
            return None

        readings = self._points[:, 0]
        mappings = self._points[:, 1]

        # find nearest neighbor
        idx = np.argmin(np.abs(readings - inputValue))
        return mappings[idx]


    def getFileName(self):
        return self._activeCalibrationName