# PicoScope Measurement

The goal of the project is to create a simple application that can measure and display
multiple channels using PicoScope oscilloscope.

It should be able to handle:
- up to 8 channels
- Up to 10 million points per channel
- Display the measured data at high rate.
- Optionally select a processing method for the data.

## Specification

### PicoScope

- PicoScope 4824

### GUI

- Buttons: start, stop, exit
- Input fields: Sampling frequency [Hz], Samling time [s], Number of channels
- Plot: y(t) vs t
- Output fields: Average frame rate [Hz], Average processing time [ms]