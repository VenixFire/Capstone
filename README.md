# Capstone
VandalOptics capstone project.
Datalogger and backend developed by Jack Chambers.


## Target Devices
Intended platform is Raspberry Pi (4b) using headless debian with latest version. 
Datalogger interfaces with Thorlabs PM60 Optic Power Meter to read optical power levels.


## Libraries & Packages
### Python Libraries
- PyVisa (SCPI)
- Numpy
- Flask

### Packages
- avahi-daemon (dns masking for http)
- nmcli (enabling wifi access point; native on newer debian versions)

### Necessary Setup
It's necessary when deploying on Linux to provide proper read/write access to the power meter peripheral.

## Todo List
- [x] Power Meter SCPI Interface
- [x] Calibrations
- [x] Result Logging
- [ ] Error Logging
- [ ] Device Information
- [x] HTTP Content Service
- [ ] Reformat all that for clarity / readability

## Important References
USB Power Control
[https://github.com/mvp/uhubctl](https://github.com/mvp/uhubctl) 

## Credentials
Raspberry Pi
> logger@vandaloptics
> vandals

Wi-Fi
> VandalOptics
> GoVandals!

## Notes
- Volume should be a polynomial, I forget what shape, but it's not a linear fit.
- Need to experiment, but it might spawn two apps
- Pipe the output to a logfile, so the app should add a timestamp

