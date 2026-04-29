"""
VandalOptics
Capstone Design Teams 1

Description:
    Volume estimation script using the PM61 power meter.
    Handles warmup, calibration, outlier rejection, and live volume reading.

Dependencies:
    PowerMeter.py (must be in the same directory)
    numpy

Authors:
    Capstone Team 1
"""

import numpy as np
import time
import json
import os
from collections import deque
from PowerMeter import PowerMeter, MODE_WATT, USB_DEVICE_STRING

# ── Device Description ────────────────────────────────────────────────────────

DEVICE_DESCRIPTION_FILE = os.path.join(
    os.path.dirname(__file__), "..", "DeviceData", "DeviceDescription.json"
)

def load_device_description() -> dict:
    """Load the device description JSON, which defines filenames for cal and results."""
    path = os.path.abspath(DEVICE_DESCRIPTION_FILE)
    if not os.path.exists(path):
        raise FileNotFoundError(f"DeviceDescription.json not found at: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def get_data_paths() -> tuple[str, str]:
    """
    Read CalibrationFile and ResultsFile from DeviceDescription.json.
    Returns absolute paths for (calibration_file, results_file).
    """
    desc = load_device_description()

    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "DeviceData"))

    cal_filename     = desc["CalibrationFile"]
    results_filename = desc["ResultsFile"]

    cal_path     = os.path.join(base, "Calibrations",       cal_filename)
    results_path = os.path.join(base, "MeasurementResults", results_filename)

    return cal_path, results_path

# ── Configuration ────────────────────────────────────────────────────────────

WAVELENGTH_NM       = 870
MEASUREMENT_RANGE   = 2.06e-6       # 2.06 µW range — matches your current setup
WARMUP_SECONDS      = 1800          # 30 min warmup, skip with Ctrl+C if already warm

SAMPLES_PER_READ    = 150           # samples averaged per measurement
SAMPLE_DELAY        = 0.05          # seconds between samples (20 Hz)
OUTLIER_SIGMA       = 2.5           # MAD sigma threshold for spike rejection

CAL_LEVELS          = [0, 20, 40, 60, 80, 100]   # % volume levels

# ── Noise-Robust Reading ──────────────────────────────────────────────────────

def collect_samples(meter: PowerMeter, n=SAMPLES_PER_READ, delay=SAMPLE_DELAY) -> np.ndarray:
    """Collect n raw power readings from the meter."""
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
        return float('nan'), float('nan'), 0

    med = np.median(data)
    mad = np.median(np.abs(data - med)) * 1.4826  # scaled MAD ≈ std dev for Gaussian

    # guard against zero MAD (all samples identical — quantization floor)
    if mad == 0:
        return float(np.mean(data)), 0.0, len(data)

    mask = np.abs(data - med) < sigma * mad
    clean = data[mask]
    return float(np.mean(clean)), float(np.std(clean)), int(mask.sum())


def stable_reading(meter: PowerMeter) -> tuple[float, float]:
    """
    Collect samples and return a robust (mean, std) power reading in Watts.
    Prints a brief quality report.
    """
    data = collect_samples(meter)
    mean, std, n_clean = robust_mean(data)
    rejected = len(data) - n_clean
    print(f"  Reading: {mean:.4e} W  (±{std:.2e}, {rejected} spikes rejected / {len(data)} samples)")
    return mean, std


def warmup(seconds=WARMUP_SECONDS):
    """Wait for source and meter to thermally stabilize."""
    print(f"\nWaiting {seconds // 60} min for thermal warmup...")
    print("(Press Ctrl+C to skip if already warmed up)\n")
    try:
        for remaining in range(seconds, 0, -30):
            print(f"  {remaining // 60}m {remaining % 60:02d}s remaining...", end='\r')
            time.sleep(30)
    except KeyboardInterrupt:
        print("\n  Warmup skipped.")


def run_calibration(meter: PowerMeter, cal_path: str) -> dict:
    """
    Interactive calibration: prompts user to set each fill level,
    collects stable readings, saves to cal_path.
    Returns calibration table {volume_pct: power_watts}.
    """
    print("\n── Calibration ─────────────────────────────────────────────")
    print(f"You will be prompted to set {len(CAL_LEVELS)} fill levels.")
    print("Hold each level steady. More samples = better accuracy.\n")

    cal_table = {}

    for level in CAL_LEVELS:
        input(f"  Set tank to {level:3d}% full, then press Enter...")
        mean, std = stable_reading(meter)
        cal_table[level] = mean

        # warn if noise is high relative to the signal range so far
        if len(cal_table) > 1:
            values = list(cal_table.values())
            dynamic_range = max(values) - min(values)
            if dynamic_range > 0 and std / dynamic_range > 0.1:
                print(f"  ! Warning: noise (±{std:.2e}) is >10% of current dynamic range ({dynamic_range:.2e} W)")
                print(f"    Consider more samples or checking fiber connections.")

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

    # Ensure directory exists and save
    os.makedirs(os.path.dirname(cal_path), exist_ok=True)
    with open(cal_path, 'w') as f:
        json.dump(cal_table, f, indent=2)
    print(f"\nCalibration saved to {cal_path}")

    return cal_table


def load_calibration(cal_path: str) -> dict | None:
    """Load calibration from file if it exists."""
    if not os.path.exists(cal_path):
        return None
    with open(cal_path, 'r') as f:
        raw = json.load(f)
    # JSON keys are strings — convert back to int
    cal = {int(k): v for k, v in raw.items()}
    print(f"Loaded calibration from {cal_path}")
    return cal


def estimate_volume(power_w: float, cal_table: dict) -> float:
    """
    Interpolate volume % from a power reading using the calibration table.
    Assumes power decreases monotonically as volume increases (more bend = more loss).
    Clamps output to [0, 100].
    """
    levels = np.array(sorted(cal_table.keys()))          # [0, 25, 50, 75, 100]
    powers = np.array([cal_table[l] for l in levels])    # corresponding power values

    # Power decreases as volume increases, so flip for np.interp (needs ascending x)
    if powers[0] > powers[-1]:
        volume = np.interp(power_w, powers[::-1], levels[::-1])
    else:
        # If power increases with volume (unexpected but handle it)
        volume = np.interp(power_w, powers, levels)

    return float(np.clip(volume, 0, 100))


class VolumeReader:
    """
    Maintains a rolling buffer of volume estimates for smoothing.
    Use update() to add new estimates, get() to read the smoothed value.
    """
    def __init__(self, window=5):
        self.buf = deque(maxlen=window)

    def update(self, volume_pct: float):
        self.buf.append(volume_pct)

    def get(self) -> float:
        return float(np.mean(self.buf)) if self.buf else float('nan')


def record_measurement(results_path: str, power: float, volume_raw: float, volume_est: float) -> None:
    """
    Append a single measurement entry to the results file in realtime.
    The file is kept as a valid JSON array at all times.
    """
    entry = {
        "timestamp":  time.time(),
        "reading":    power,
        "volume_raw": volume_raw,
        "volume_est": volume_est,
    }

    os.makedirs(os.path.dirname(results_path), exist_ok=True)

    # If file doesn't exist yet, start a fresh array
    if not os.path.exists(results_path):
        with open(results_path, 'w') as f:
            json.dump([entry], f, indent=2)
        return

    # Otherwise: strip the closing ] and append
    with open(results_path, 'r+') as f:
        f.seek(0, os.SEEK_END)
        pos = f.tell()

        # Walk back to find the closing ]
        while pos > 0:
            pos -= 1
            f.seek(pos)
            ch = f.read(1)
            if ch == ']':
                break

        # Overwrite from ] onward with ,\n  <entry>\n]
        f.seek(pos)
        f.write(',\n  ' + json.dumps(entry) + '\n]')
        f.truncate()


def main():
    # Resolve file paths from device description before doing anything else
    cal_path, results_path = get_data_paths()

    meter = PowerMeter(deviceId=USB_DEVICE_STRING, cmdLogEnb=False)
    meter.connect()

    meter.setMeasurementUnit(MODE_WATT)
    meter.setWavelength(WAVELENGTH_NM)
    meter.setMeasurementRange(MEASUREMENT_RANGE)

    # Warmup
    warmup()

    # Calibration: load existing or run new
    cal_table = load_calibration(cal_path)
    if cal_table is None:
        print("No calibration file found.")
        cal_table = run_calibration(meter, cal_path)
    else:
        redo = input("Run new calibration? (y/N): ").strip().lower()
        if redo == 'y':
            cal_table = run_calibration(meter, cal_path)

    # Live reading loop
    print("\n── Live Volume Readings ─────────────────────────────────────")
    print(f"Recording to {results_path}. Press Ctrl+C to stop.\n")

    smoother = VolumeReader(window=5)

    try:
        while True:
            power, std = stable_reading(meter)
            volume = estimate_volume(power, cal_table)
            smoother.update(volume)
            smoothed = smoother.get()

            record_measurement(results_path, power, volume, smoothed)
            print(f"  Volume: {smoothed:6.1f}%  (raw: {volume:.1f}%  power: {power:.4e} W)")

    except KeyboardInterrupt:
        print("\nStopping.")
        meter.disconnect()


if __name__ == "__main__":
    main()