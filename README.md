# Capstone
VandalOptics capstone project.
Datalogger and backend developed by Jack Chambers.


## Target Devices
Intended platform is Raspberry Pi (4b) using headless debian with latest version. 
Datalogger interfaces with Thorlabs PM60 Optic Power Meter to read optical power levels.

## Setup
Note: this is designed for a specific PM61 power meter, I didn't include any way to customize the specific serial number of your device. Please see `VolumeSensorHeadless.py` and `install.sh` to update the specific VendorId, DeviceId, and SerialNumber for your device.

### Debian Install
Create a new image of debian, this was executed on debian trixie, create a user named `logger` and set the password to whatever you want.


### Clone The Repository
Clone the repository to the home directory of the `logger` user:
```git clone https://github.com/VenixFire/Capstone```


### Run Install Script
Just run `./install.sh` and it should install all the relevant packages, services, and scripts to start the logger and webserver.

Make sure to run `python3 ./src/CalibrationTool.py` to create an initial calibration.


### View Results
You can navigate to `hostname:5000` after connecting to the WiFi and view live results and readings, create new measurement files, and view logs from device activity.
