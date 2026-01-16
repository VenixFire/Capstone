
import sys
import csv
from pathlib import Path

class Calibration:
    def __init__(self, metric, calDir="./cal", calPrefix="CAL_"):
        self._calDirectory = calDir

        fileName = f"{calPrefix}{metric}.csv"
        filePath = Path(self._calDirectory) / fileName

        if not filePath.exists():
            raise FileNotFoundError(f"Calibration file not found: {filePath}")

        self._calData = []

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
                self._calData.append({
                    "Reading": float(row["Reading"]),
                    "Result": float(row["Result"]),
                    "Unit": row["Unit"]
                })

    def get(self, reading : float):
        pass