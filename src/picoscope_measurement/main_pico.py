from PySide6.QtCore import QTimer
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from picosdk.ps4000a import ps4000a as ps
from picosdk.functions import adc2mV, assert_pico_ok
import ctypes
import time

from src.gui_tools.daq_window import DAQWindow
from src.common.utils import scale_adc_two_complement


class PicoScopeApp(DAQWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PicoScope Measurement")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_measurement)

        # GUI parameters
        self.num_channels_ui = None
        self.sampling_time_ui = None
        self.sampling_freq_ui = None

        # Plots
        self.figure = None
        self.ax = None
        self.canvas = None

        # PicoScope variables
        self.c_handle = ctypes.c_int16()
        self.status = {}
        self.pico_opened = False

        # Measurement variables
        self.num_samples = None
        self.preTriggerSamples = None
        self.postTriggerSamples = None
        self.timebase = None
        self.dt_ns = None
        self.buffers = None
        self.max_adc = None
        self.num_channels = None
        self.values = []

        # Setup parameter list and plots
        self.setup_parameter_list()
        self.setup_plots()

    def setup_parameter_list(self):
        self.num_channels_ui = self.add_parameter("Number of Channels", 4)
        self.sampling_time_ui = self.add_parameter("Sampling Time (s)", 1)
        self.sampling_freq_ui = self.add_parameter("Sampling Frequency (Hz)", 1000000)

    def setup_plots(self):
        self.canvas, self.figure, self.ax = self.add_pyplot_tab("Waveforms")
        # self.figure, self.ax = plt.subplots()
        # self.canvas = FigureCanvas(self.figure)
        # self.add_widget_tab(self.canvas, "Waveforms")

    def run_block_capture(self):
        self.status["runBlock"] = ps.ps4000aRunBlock(
            self.c_handle,
            self.preTriggerSamples,
            self.postTriggerSamples,
            self.timebase,
            None,
            0,
            None,
            None
        )
        assert_pico_ok(self.status["runBlock"])

    def start_measurement(self):
        print("Starting measurement")
        # Configuration paramteres
        self.num_channels = self.get_int_parameter_value(self.num_channels_ui)
        sampling_time = self.get_float_parameter_value(self.sampling_time_ui)
        sampling_freq = self.get_int_parameter_value(self.sampling_freq_ui)
        channel_range = 7  # PS4000A_2V

        # Open PicoScope
        self.status["open_unit"] = ps.ps4000aOpenUnit(ctypes.byref(self.c_handle), None)
        assert_pico_ok(self.status["open_unit"])
        print(f"Picoscope opened: handle: {self.c_handle.value}")

        # Configure channels
        for i in range(self.num_channels):
            channel = i  # Use channel number directly
            self.status[f"setChA{i}"] = ps.ps4000aSetChannel(
                self.c_handle,
                channel,
                1,  # enabled
                1,  # dc coupled
                channel_range,
                0.0  # analogue offset
            )
            assert_pico_ok(self.status[f"setChA{i}"])

        # Set up trigger
        self.status["setSimpleTrigger"] = ps.ps4000aSetSimpleTrigger(
            self.c_handle,
            1,  # enabled
            0,  # source
            1024,  # threshold
            2,  # direction
            0,  # delay
            1000  # auto trigger time
        )
        assert_pico_ok(self.status["setSimpleTrigger"])

        self.timebase = int((80000000.0/sampling_freq) - 1)
        sampling_freq = 1 / (self.timebase + 1) * 80000000
        print(f"Timebase: {self.timebase}, sampling frequency: {sampling_freq}")

        # Set number of pre- and post-trigger samples to be collected
        self.num_samples = int(sampling_freq * sampling_time)
        self.preTriggerSamples = self.num_samples // 2
        self.postTriggerSamples = self.num_samples // 2
        max_samples = self.preTriggerSamples + self.postTriggerSamples

        print(f"Num samples: {self.num_samples}, pre-trigger: {self.preTriggerSamples}, post-trigger: {self.postTriggerSamples}")


        # Get timebase information
        time_interval_ns = ctypes.c_float()
        returned_max_samples = ctypes.c_int32()
        self.status["getTimebase2"] = ps.ps4000aGetTimebase2(
            self.c_handle,
            self.timebase,
            max_samples,
            ctypes.byref(time_interval_ns),
            ctypes.byref(returned_max_samples),
            0
        )
        self.dt_ns = time_interval_ns.value

        # Start measurement
        self.pico_opened = True
        self.run_block_capture()
        self.timer.start(50)  # Update every 50 ms

    def update_measurement(self):
        if not self.pico_opened:
            return
        start_time = time.time()

        # Check if ready
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        self.status["isReady"] = ps.ps4000aIsReady(self.c_handle, ctypes.byref(ready))
        # Return if not ready
        if ready.value == check.value:
            return

        # Set data buffers

        self.buffers = [np.zeros(self.num_samples, dtype=np.int16) for _ in range(self.num_channels)]
        for i, buffer in enumerate(self.buffers):
            self.status[f"setDataBufferA{i}"] = ps.ps4000aSetDataBuffer(
                self.c_handle,
                i,  # channel
                buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                self.num_samples,
                0,  # segment index
                0  # ratio mode
            )
            assert_pico_ok(self.status[f"setDataBufferA{i}"])

        # Get data from scope
        cmax_samples = ctypes.c_int32(self.num_samples)
        for i, buffer in enumerate(self.buffers):
            self.status[f"getValues{i}"] = ps.ps4000aGetValues(
                self.c_handle,
                i,  # channel
                ctypes.byref(cmax_samples),
                0,  # downSampleRatio
                0,  # downSampleRatioMode
                0,  # segment index
                None  # overflow
            )
            assert_pico_ok(self.status[f"getValues{i}"])

        # Get maximum ADC value
        self.max_adc = ctypes.c_int16()
        self.status["maximumValue"] = ps.ps4000aMaximumValue(self.c_handle, ctypes.byref(self.max_adc))
        assert_pico_ok(self.status["maximumValue"])

        # convert buffers to Voltage and store in self.values
        self.values = []
        for i, buffer in enumerate(self.buffers):
            values = scale_adc_two_complement(buffer[:cmax_samples.value], 16, 2.0)
            self.values.append(values)
        # calculate time axis
        dt_s = self.dt_ns * 1e-9
        time_axis = np.linspace(- self.preTriggerSamples * dt_s
                           , (self.postTriggerSamples - 1) * dt_s, self.preTriggerSamples+self.postTriggerSamples)
        # time = np.linspace(0, (cmaxSamples.value - 1) * timeIntervalns.value, cmaxSamples.value)
        time_axis = time_axis[:cmax_samples.value]

        # Process and update plot
        self.ax.clear()
        # Create time data

        for i, values in enumerate(self.values):
            # Convert ADC counts to millivolts
            channel_range = 7  # PS4000A_2V
            self.ax.plot(time_axis, values, label=f"Channel {i}")

        self.ax.legend()
        self.canvas.draw()

        # Update output fields
        end_time = time.time()
        processing_time = (end_time - start_time) * 1000
        # self.processing_time_label.setText(f"Average Processing Time: {processing_time:.2f} ms")
        # self.frame_rate_label.setText(f"Average Frame Rate: {1 / (end_time - start_time):.2f} Hz")

        self.process_data(time_axis, self.values)

        # Start next acquisition
        self.run_block_capture()

    def stop_measurement(self):
        if hasattr(self, 'c_handle') and self.pico_opened:
            print("Stopping measurement")
            self.status["stop"] = ps.ps4000aStop(self.c_handle)
            assert_pico_ok(self.status["stop"])
            self.status["close"] = ps.ps4000aCloseUnit(self.c_handle)
            assert_pico_ok(self.status["close"])
            self.pico_opened = False
        else:
            print("Not running")
        self.timer.stop()

    def save_data(self):
        print(f"Saving data to: {self.save_path.text()}")

    def close_daq(self):
        self.stop_measurement()
        print("Closing DAQ")


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = PicoScopeApp()
    window.show()
    app.exec()