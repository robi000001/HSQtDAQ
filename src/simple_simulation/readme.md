# Simple Simulation

The goal of the project is to create a python application that only simulates the data acquisition.

It should be able to handle:
- 16 channels
- 10 kHz of sampling frequency on all channels at the same time
- Display the measured data at 10 Hz, each iteration it should display 1000 measured data points/channel.

## Specification

### GUI

- Buttons: start, stop, exit
- Input fields: Sampling frequency [Hz], Samling time [s], Update rate [Hz], Number of channels, Number of channels per plot
- Plot: y(t) vs t
- Output fields: Frame rate [Hz], Processing time [ms]
