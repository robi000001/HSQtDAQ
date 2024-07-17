# Simple Simulation

The goal of the project is to create a python application that measures analogue data using National Instruments DAQmx compatible hardware.

It should be able to handle:
- up to 16 channels
- 10 kHz of sampling frequency on all channels at the same time
- Display the measured data at high speed
- Aquisition mode: finite samples
- Using official NI DAQmx Python API

## Specification

### GUI

- Buttons: start, stop, exit
- Input fields: Sampling frequency [Hz], Samling time [s], Number of channels, Voltage range [V]
- Plot: y(t) vs t
- Output fields: Average frame rate [Hz], Average processing time [ms] (both since start)
