# Capstone
VandalOptics capstone project.

`/raspi_src/` contains source code for datalogger

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

## Todo List
- [x] Power Meter SCPI Interface
- [ ] Calibrations
- [ ] Result Logging
- [ ] Error Logging
- [ ] Device Information
- [ ] HTTP Content Service
- [ ] Reformat all that for clarity / readability

## Important References
USB Power Control
[https://github.com/mvp/uhubctl](https://github.com/mvp/uhubctl) 

## Notes
- Volume should be a polynomial, I forget what shape, but it's not a linear fit.
- Need to experiment, but it might spawn two apps
- Pipe the output to a logfile, so the app should add a timestamp

