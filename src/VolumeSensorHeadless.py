"""
VandalOptics
Capstone Design Teams 1

Description:
    Headless volume estimation script using the PM61 power meter.
    Reads configuration from DeviceDescription.json, loads calibration from disk,
    and runs the measurement loop without any user interaction.

    All output is written to both stdout and a timestamped .log file under
    DeviceData/Logs/.

    Exit conditions:
        SIGINT / Ctrl+C  — clean shutdown
        Missing calibration file — exits with error

Dependencies:
    PowerMeter.py (must be in the same directory)
    numpy

Usage:
    python VolumeSensorHeadless.py

Authors:
    Capstone Team 1
"""

import numpy as np
import time
import json
import os
import sys
from collections import deque
from datetime import datetime
from PowerMeter import PowerMeter, MODE_WATT, USB_DEVICE_STRING

# ── Configuration ─────────────────────────────────────────────────────────────

WAVELENGTH_NM     = 870
MEASUREMENT_RANGE = 2.06e-6   # 2.06 µW range
SAMPLES_PER_READ  = 150       # samples averaged per measurement
SAMPLE_DELAY      = 0.05      # seconds between samples (20 Hz)
OUTLIER_SIGMA     = 2.5       # MAD sigma threshold for spike rejection

# ── Paths ─────────────────────────────────────────────────────────────────────

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "DeviceData"))

DEVICE_DESCRIPTION_FILE = os.path.join(BASE_DIR, "DeviceDescription.json")


def get_logs_dir() -> str:
    return os.path.join(BASE_DIR, "Logs")

# ── Logging ───────────────────────────────────────────────────────────────────

class TeeLogger:
    """
    Writes every log() call to both stdout and an open log file.
    Also redirects stderr so uncaught exceptions appear in the log.
    """

    def __init__(self, log_path: str):
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        self._file   = open(log_path, "w", buffering=1)  # line-buffered
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        sys.stderr   = self  # redirect stderr so tracebacks also go to the log

    def log(self, message: str) -> None:
        ts   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{ts}  {message}"
        print(line, file=self._stdout)
        print(line, file=self._file)

    # Make TeeLogger usable as a stderr replacement (write / flush interface)
    def write(self, message: str) -> None:
        if message.strip():
            self.log(f"[STDERR] {message.rstrip()}")
        else:
            self._file.flush()

    def flush(self) -> None:
        self._stdout.flush()
        self._file.flush()

    def close(self) -> None:
        sys.stderr = self._stderr
        self._file.close()


def make_log_path() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(get_logs_dir(), f"VolumeSensorHeadless_{timestamp}.txt")

# ── Device Description ────────────────────────────────────────────────────────

def load_device_description() -> dict:
    if not os.path.exists(DEVICE_DESCRIPTION_FILE):
        print(f"[ERROR] DeviceDescription.json not found at: {DEVICE_DESCRIPTION_FILE}",
              file=sys.stderr)
        sys.exit(1)
    with open(DEVICE_DESCRIPTION_FILE, "r") as f:
        return json.load(f)


def get_data_paths() -> tuple[str, str]:
    """
    Read CalibrationFile and ResultsFile from DeviceDescription.json.
    Returns absolute paths for (calibration_file, results_file).
    """
    desc         = load_device_description()
    cal_path     = os.path.join(BASE_DIR, "Calibrations",       desc["CalibrationFile"])
    results_path = os.path.join(BASE_DIR, "MeasurementResults", desc["ResultsFile"])
    return cal_path, results_path

# ── Sampling ──────────────────────────────────────────────────────────────────

def collect_samples(meter: PowerMeter, logger: TeeLogger,
                    n=SAMPLES_PER_READ, delay=SAMPLE_DELAY) -> np.ndarray:
    samples = []
    for _ in range(n):
        try:
            samples.append(meter.getPowerReading())
        except Exception as e:
            logger.log(f"[WARN]  Read error: {e}")
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


def stable_reading(meter: PowerMeter, logger: TeeLogger) -> tuple[float, float]:
    data = collect_samples(meter, logger)
    mean, std, n_clean = robust_mean(data)
    rejected = len(data) - n_clean
    logger.log(f"[READ]  {mean:.4e} W  ±{std:.2e}  ({rejected} spikes / {len(data)} samples)")
    return mean, std

# ── Calibration ───────────────────────────────────────────────────────────────

def load_calibration(cal_path: str, logger: TeeLogger) -> dict:
    if not os.path.exists(cal_path):
        logger.log(f"[ERROR] Calibration file not found: {cal_path}")
        logger.log("[ERROR] Run VolumeSensor.py first to generate a calibration.")
        logger.close()
        sys.exit(1)
    with open(cal_path, "r") as f:
        raw = json.load(f)
    # JSON keys are strings — convert back to int
    return {int(k): v for k, v in raw.items()}

# ── Volume Estimation ─────────────────────────────────────────────────────────

def estimate_volume(power_w: float, cal_table: dict) -> float:
    levels = np.array(sorted(cal_table.keys()))
    powers = np.array([cal_table[l] for l in levels])

    if powers[0] > powers[-1]:
        volume = np.interp(power_w, powers[::-1], levels[::-1])
    else:
        volume = np.interp(power_w, powers, levels)

    return float(np.clip(volume, 0, 100))


class VolumeReader:
    """Rolling average smoother for volume estimates."""
    def __init__(self, window=5):
        self.buf = deque(maxlen=window)

    def update(self, volume_pct: float):
        self.buf.append(volume_pct)

    def get(self) -> float:
        return float(np.mean(self.buf)) if self.buf else float("nan")

# ── Results Recording ─────────────────────────────────────────────────────────

def record_measurement(results_path: str, power: float,
                        volume_raw: float, volume_est: float) -> None:
    entry = {
        "timestamp":  time.time(),
        "reading":    power,
        "volume_raw": volume_raw,
        "volume_est": volume_est,
    }

    os.makedirs(os.path.dirname(results_path), exist_ok=True)

    if not os.path.exists(results_path):
        with open(results_path, "w") as f:
            json.dump([entry], f, indent=2)
        return

    with open(results_path, "r+") as f:
        f.seek(0, os.SEEK_END)
        pos = f.tell()
        while pos > 0:
            pos -= 1
            f.seek(pos)
            if f.read(1) == "]":
                break
        f.seek(pos)
        f.write(",\n  " + json.dumps(entry) + "\n]")
        f.truncate()

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log_path = make_log_path()
    logger   = TeeLogger(log_path)

    logger.log(f"[INFO]  Log file      : {log_path}")

    cal_path, results_path = get_data_paths()
    logger.log(f"[INFO]  Calibration   : {cal_path}")
    logger.log(f"[INFO]  Results       : {results_path}")

    cal_table = load_calibration(cal_path, logger)
    logger.log(f"[INFO]  Calibration loaded ({len(cal_table)} levels)")

    meter = PowerMeter(deviceId=USB_DEVICE_STRING, cmdLogEnb=False, logger=logger)

    while meter.isConnected() == False:
        meter.connect()
    
    meter.setMeasurementUnit(MODE_WATT)
    meter.setWavelength(WAVELENGTH_NM)
    meter.setMeasurementRange(MEASUREMENT_RANGE)
    logger.log("[INFO]  Meter connected. Starting measurement loop.")

    smoother = VolumeReader(window=5)

    try:
        while True:
            power, _ = stable_reading(meter, logger)
            volume_raw = estimate_volume(power, cal_table)
            smoother.update(volume_raw)
            volume_est = smoother.get()

            record_measurement(results_path, power, volume_raw, volume_est)
            logger.log(f"[VOL]   {volume_est:6.1f}%  (raw: {volume_raw:.1f}%  power: {power:.4e} W)")

    except KeyboardInterrupt:
        logger.log("[INFO]  Shutting down.")
    finally:
        meter.disconnect()
        logger.close()


if __name__ == "__main__":
    main()