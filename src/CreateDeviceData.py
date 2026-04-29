"""
VandalOptics
Capstone Design Team 1
Device Data Creation Automation
"""

import json
import os
import sys

# ── Paths ─────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "DeviceData"))

DIRECTORIES = [
    BASE_DIR,
    os.path.join(BASE_DIR, "Calibrations"),
    os.path.join(BASE_DIR, "MeasurementResults"),
]

DEVICE_DESCRIPTION_PATH = os.path.join(BASE_DIR, "DeviceDescription.json")

DEFAULT_DESCRIPTION = {
    "DeviceName":      "VandalOptics Device",
    "CalibrationFile": "calibration.json",
    "ResultsFile":     "results.json",
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def create_directory(path: str) -> None:
    if os.path.isdir(path):
        print(f"  [skip]    {path}")
    else:
        os.makedirs(path)
        print(f"  [created] {path}")


def create_device_description(path: str) -> None:
    if os.path.exists(path):
        print(f"  [skip]    {path}")
        return

    with open(path, "w") as f:
        json.dump(DEFAULT_DESCRIPTION, f, indent=2)
    print(f"  [created] {path}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("VandalOptics — Setup")
    print("====================\n")

    print("Creating directories:")
    for d in DIRECTORIES:
        create_directory(d)

    print("\nCreating device description:")
    create_device_description(DEVICE_DESCRIPTION_PATH)

    print("\nSetup complete.")
    print(f"\nDefault device description written to:")
    print(f"  {DEVICE_DESCRIPTION_PATH}")
    print(f"\nEdit DeviceDescription.json or use the web settings page to configure")
    print(f"the device name, calibration file, and results file.")


if __name__ == "__main__":
    main()