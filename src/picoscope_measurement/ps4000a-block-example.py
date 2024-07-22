import ctypes
import numpy as np
from picosdk.ps4000a import ps4000a as ps
import matplotlib.pyplot as plt
from picosdk.functions import adc2mV, assert_pico_ok

# Create status ready for use
status = {}

# Open 4000 series PicoScope
handle = ctypes.c_int16()
status["openunit"] = ps.ps4000aOpenUnit(ctypes.byref(handle), None)
assert_pico_ok(status["openunit"])

# Set up channel A
chARange = 7  # 2V range
status["setChA"] = ps.ps4000aSetChannel(handle, 0, 1, 1, chARange, 0)
assert_pico_ok(status["setChA"])

# Set up channel B
chBRange = 7  # 2V range
status["setChB"] = ps.ps4000aSetChannel(handle, 1, 1, 1, chBRange, 0)
assert_pico_ok(status["setChB"])

# Set up single trigger
status["trigger"] = ps.ps4000aSetSimpleTrigger(handle, 1, 0, 1024, 2, 0, 1000)
assert_pico_ok(status["trigger"])

# Set number of pre and post trigger samples to be collected
preTriggerSamples = 20000
postTriggerSamples = 20000
maxSamples = preTriggerSamples + postTriggerSamples

# Get timebase information
timebase = 8
timeIntervalns = ctypes.c_float()
returnedMaxSamples = ctypes.c_int32()
status["getTimebase2"] = ps.ps4000aGetTimebase2(handle, timebase, maxSamples, ctypes.byref(timeIntervalns), ctypes.byref(returnedMaxSamples), 0)
assert_pico_ok(status["getTimebase2"])

# Run block capture
status["runBlock"] = ps.ps4000aRunBlock(handle, preTriggerSamples, postTriggerSamples, timebase, None, 0, None, None)
assert_pico_ok(status["runBlock"])

# Check for data collection to finish using ps4000aIsReady
ready = ctypes.c_int16(0)
check = ctypes.c_int16(0)
while ready.value == check.value:
    status["isReady"] = ps.ps4000aIsReady(handle, ctypes.byref(ready))

# Create buffers ready for data
bufferAMax = (ctypes.c_int16 * maxSamples)()
bufferBMax = (ctypes.c_int16 * maxSamples)()

# Set data buffers
status["setDataBuffersA"] = ps.ps4000aSetDataBuffers(handle, 0, ctypes.byref(bufferAMax), None, maxSamples, 0, 0)
assert_pico_ok(status["setDataBuffersA"])

status["setDataBuffersB"] = ps.ps4000aSetDataBuffers(handle, 1, ctypes.byref(bufferBMax), None, maxSamples, 0, 0)
assert_pico_ok(status["setDataBuffersB"])

# Get data from scope
cmaxSamples = ctypes.c_int32(maxSamples)
status["getValues"] = ps.ps4000aGetValues(handle, 0, ctypes.byref(cmaxSamples), 0, 0, 0, None)
assert_pico_ok(status["getValues"])

# Get maximum ADC value
maxADC = ctypes.c_int32()
status["maximumValue"] = ps.ps4000aMaximumValue(handle, ctypes.byref(maxADC))
assert_pico_ok(status["maximumValue"])
print("Max ADC value: ", maxADC)

# Convert ADC counts data to mV
adc2mVChA = adc2mV(bufferAMax, chARange, maxADC)
adc2mVChB = adc2mV(bufferBMax, chBRange, maxADC)

# Create time data
time = np.linspace(0, (cmaxSamples.value - 1) * timeIntervalns.value, cmaxSamples.value)

# Plot data from channel A and B
plt.plot(time, adc2mVChA[:])
plt.plot(time, adc2mVChB[:])
plt.xlabel('Time (ns)')
plt.ylabel('Voltage (mV)')
plt.show()

# Stop the scope
status["stop"] = ps.ps4000aStop(handle)
assert_pico_ok(status["stop"])

# Close the scope
status["close"] = ps.ps4000aCloseUnit(handle)
assert_pico_ok(status["close"])

# Display status returns
print(status)