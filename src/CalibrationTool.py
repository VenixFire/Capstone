"""
VandalOptics
Capstone Design Teams 1

Description:
    Standalone calibration script using the PM61 power meter.
    Prompts for an output filename, then walks through each fill level
    and saves the resulting calibration to DeviceData/Calibrations/.

Dependencies:
    PowerMeter.py (must be in the same directory)
    numpy

Usage:
    python Calibrate.py

Authors:
    Capstone Team 1
"""

import numpy as np
import time
import json
import os
import sys
from PowerMeter import PowerMeter, MODE_WATT, USB_DEVICE_STRING

# ── Configuration ─────────────────────────────────────────────────────────────

WAVELENGTH_NM     = 870
MEASUREMENT_RANGE = 2.06e-6   # 2.06 µW range
SAMPLES_PER_READ  = 150       # samples averaged per measurement
SAMPLE_DELAY      = 0.05      # seconds between samples (20 Hz)
OUTLIER_SIGMA     = 2.5       # MAD sigma threshold for spike rejection

CAL_LEVELS        = [0, 20, 40, 60, 80, 100]   # % volume levels

CALIBRATIONS_DIR  = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "DeviceData", "Calibrations")
)

# ── Sampling ──────────────────────────────────────────────────────────────────

def collect_samples(meter: PowerMeter, n=SAMPLES_PER_READ, delay=SAMPLE_DELAY) -> np.ndarray:
    samples = []
    for _ in range(n):
        try:
            samples.append(meter.getPowerReading())
        except Exception as e:
            print(f"  ! Read error: {e}")
        time.sleep(delay)
    return np.array(samples)


def robust_mean(data: np.ndarray, sigma=OUTLIER_SIGMA) -> tuple[float, float, int]:
    """
    Reject outliers using Median Absolute Deviation, then return mean.
    Returns: (mean, std_dev, n_clean_samples)
    """
    if len(data) == 0:
        return float("nan"), float("nan"), 0

    med = np.median(data)
    mad = np.median(np.abs(data - med)) * 1.4826  # scaled MAD ≈ std dev for Gaussian

    if mad == 0:
        return float(np.mean(data)), 0.0, len(data)

    mask = np.abs(data - med) < sigma * mad
    clean = data[mask]
    return float(np.mean(clean)), float(np.std(clean)), int(mask.sum())


def stable_reading(meter: PowerMeter) -> tuple[float, float]:
    data = collect_samples(meter)
    mean, std, n_clean = robust_mean(data)
    rejected = len(data) - n_clean
    print(f"  Reading: {mean:.4e} W  (±{std:.2e}, {rejected} spikes rejected / {len(data)} samples)")
    return mean, std

# ── Filename Prompt ───────────────────────────────────────────────────────────

def prompt_filename() -> str:
    """
    Ask the user for a calibration filename.
    Appends .json if not already present.
    Warns if the file already exists and asks for confirmation before overwriting.
    """
    os.makedirs(CALIBRATIONS_DIR, exist_ok=True)

    while True:
        name = input("Enter calibration filename (without path): ").strip()

        if not name:
            print("  Filename cannot be empty. Please try again.")
            continue

        if not name.endswith(".json"):
            name += ".json"

        # Sanitise — no directory separators allowed
        if os.path.basename(name) != name:
            print("  Filename must not contain path separators. Please try again.")
            continue

        full_path = os.path.join(CALIBRATIONS_DIR, name)

        if os.path.exists(full_path):
            confirm = input(f"  '{name}' already exists. Overwrite? (y/N): ").strip().lower()
            if confirm != "y":
                print("  Please choose a different filename.")
                continue

        return full_path

# ── Calibration ───────────────────────────────────────────────────────────────

def run_calibration(meter: PowerMeter, cal_path: str) -> None:
    print("\n── Calibration ──────────────────────────────────────────────")
    print(f"Saving to: {cal_path}")
    print(f"You will be prompted to set {len(CAL_LEVELS)} fill levels.")
    print("Hold each level steady. More samples = better accuracy.\n")

    cal_table = {}

    for level in CAL_LEVELS:
        input(f"  Set tank to {level:3d}% full, then press Enter...")
        mean, std = stable_reading(meter)
        cal_table[level] = mean

        if len(cal_table) > 1:
            values = list(cal_table.values())
            dynamic_range = max(values) - min(values)
            if dynamic_range > 0 and std / dynamic_range > 0.1:
                print(f"  ! Warning: noise (±{std:.2e}) is >10% of current dynamic range ({dynamic_range:.2e} W)")
                print(f"    Consider more samples or checking fiber connections.")

    # ── Summary ───────────────────────────────────────────────────────────────

    print("\nCalibration complete:")
    print(f"  {'Level':>6}  {'Power (W)':>14}")
    print(f"  {'──────':>6}  {'──────────':>14}")
    for lvl, pwr in cal_table.items():
        print(f"  {lvl:>5}%  {pwr:>14.4e}")

    dynamic_range = max(cal_table.values()) - min(cal_table.values())
    print(f"\n  Total dynamic range: {dynamic_range:.4e} W")
    if dynamic_range < 0.01e-6:
        print("  ! Dynamic range is very small (<0.01 µW). Mechanical sensitivity may be too low.")
        print("    Consider tightening the bend radius or adding fiber wraps.")
    else:
        print("  Dynamic range looks usable.")

    with open(cal_path, "w") as f:
        json.dump(cal_table, f, indent=2)
    print(f"\nCalibration saved to {cal_path}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("VandalOptics — Calibration Tool")
    print("================================\n")

    cal_path = prompt_filename()

    meter = PowerMeter(deviceId=USB_DEVICE_STRING, cmdLogEnb=False)
    meter.connect()
    meter.setMeasurementUnit(MODE_WATT)
    meter.setWavelength(WAVELENGTH_NM)
    meter.setMeasurementRange(MEASUREMENT_RANGE)

    try:
        run_calibration(meter, cal_path)
    except KeyboardInterrupt:
        print("\n\nCalibration cancelled. No file was saved.")
        if os.path.exists(cal_path):
            os.remove(cal_path)
    finally:
        meter.disconnect()


if __name__ == "__main__":
    main()