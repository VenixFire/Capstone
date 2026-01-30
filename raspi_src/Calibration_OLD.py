
import sys
import csv
from pathlib import Path

class Calibration:
    def __init__(self, metric, calDir="./cal", calPrefix="CAL_", createNewCal=False, writeEnabled=False):
       
        rootPath = Path(__file__).parent.absolute()
        fileName = f"{calPrefix}{metric}.csv"
        relativeFilePath = Path(calDir) / fileName
        calPath = rootPath / relativeFilePath

        self._path = calPath
        self._exists = False

        
        

        if (not self._path.exists()) and (createNewCal == False):
            raise FileNotFoundError(f"Calibration file not found: {self._path}")

        self._data = []


        # define filepointer and open csv
        self._fptr = open(self._path, mode="a+", newline="", encoding="utf-8")


    def writeEntry(self, reading : float, returns : float):
        pass


    # def get(self, reading : float):
    #     pass


    # def read(self):
    #     reader = csv.DictReader(self._fptr)

    #     # Validate expected columns
    #     expectedFields = {"Reading", "Result", "Unit"}
        
    #     if not expectedFields.issubset(reader.fieldnames):
    #         raise ValueError(
    #             f"CSV must contain columns {expectedFields}, "
    #             f"found {reader.fieldnames}"
    #         )

    #     for row in reader:
    #         self._calData.append({
    #             "Reading": float(row["Reading"]),
    #             "Result": float(row["Result"]),
    #             "Unit": row["Unit"]
    #         })