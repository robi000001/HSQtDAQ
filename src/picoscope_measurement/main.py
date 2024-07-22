import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLineEdit, \
    QLabel, QMessageBox
from PySide6.QtCore import QTimer
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from picosdk.ps4000a import ps4000a as ps
from picosdk.functions import adc2mV, assert_pico_ok
import ctypes
import time


class PicoScopeApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # UI elements
        self.num_channels_ui = None
        self.sampling_time_ui = None
        self.sampling_freq_ui = None

        # PicoScope variables
        self.c_handle = ctypes.c_int16()
        self.status = {}

        # Measurement variables
        self.num_samples = None
        self.preTriggerSamples = None
        self.postTriggerSamples = None
        self.timebase = None
        self.buffers = None
        self.max_adc = None
        self.num_channels = None

        # Set up UI
        self.setWindowTitle("PicoScope Measurement")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.create_input_fields()
        self.create_buttons()
        self.create_plot()
        self.create_output_fields()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_measurement)

    def create_input_fields(self):
        input_layout = QHBoxLayout()
        self.sampling_freq_ui = QLineEdit("1000000")
        self.sampling_time_ui = QLineEdit("1")
        self.num_channels_ui = QLineEdit("4")
        input_layout.addWidget(QLabel("Sampling Frequency (Hz):"))
        input_layout.addWidget(self.sampling_freq_ui)
        input_layout.addWidget(QLabel("Sampling Time (s):"))
        input_layout.addWidget(self.sampling_time_ui)
        input_layout.addWidget(QLabel("Number of Channels:"))
        input_layout.addWidget(self.num_channels_ui)
        self.layout.addLayout(input_layout)

    def create_buttons(self):
        button_layout = QHBoxLayout()
        start_button = QPushButton("Start")
        stop_button = QPushButton("Stop")
        exit_button = QPushButton("Exit")
        start_button.clicked.connect(self.start_measurement)
        stop_button.clicked.connect(self.stop_measurement)
        exit_button.clicked.connect(self.close)
        button_layout.addWidget(start_button)
        button_layout.addWidget(stop_button)
        button_layout.addWidget(exit_button)
        self.layout.addLayout(button_layout)

    def create_plot(self):
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas)

    def create_output_fields(self):
        output_layout = QHBoxLayout()
        self.frame_rate_label = QLabel("Average Frame Rate: 0 Hz")
        self.processing_time_label = QLabel("Average Processing Time: 0 ms")
        output_layout.addWidget(self.frame_rate_label)
        output_layout.addWidget(self.processing_time_label)
        self.layout.addLayout(output_layout)

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
        try:
            # Configuration parameters
            self.num_channels = int(self.num_channels_ui.text())
            sampling_freq = int(self.sampling_freq_ui.text())
            sampling_time = float(self.sampling_time_ui.text())
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

            # Set number of pre- and post-trigger samples to be collected
            self.num_samples = int(sampling_freq * sampling_time)
            self.preTriggerSamples = self.num_samples // 2
            self.postTriggerSamples = self.num_samples // 2
            maxSamples = self.preTriggerSamples + self.postTriggerSamples

            # Get timebase information
            self.timebase = 8
            timeIntervalns = ctypes.c_float()
            returnedMaxSamples = ctypes.c_int32()
            self.status["getTimebase2"] = ps.ps4000aGetTimebase2(
                self.c_handle,
                self.timebase,
                maxSamples,
                ctypes.byref(timeIntervalns),
                ctypes.byref(returnedMaxSamples),
                0
            )

            # Start measurement
            self.run_block_capture()
            self.timer.start(50)  # Update every 50 ms

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            # Print error in details
            print(e)
            self.stop_measurement()

    def update_measurement(self):
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
        cmaxSamples = ctypes.c_int32(self.num_samples)
        for i, buffer in enumerate(self.buffers):
            self.status[f"getValues{i}"] = ps.ps4000aGetValues(
                self.c_handle,
                i,  # channel
                ctypes.byref(cmaxSamples),
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
        print(f"Maximum ADC value: {self.max_adc.value}")



        # Process and update plot
        self.ax.clear()
        for i, buffer in enumerate(self.buffers):
            # Convert ADC counts to millivolts
            channel_range = 7  # PS4000A_2V
            values = adc2mV(buffer, channel_range, self.max_adc)
            self.ax.plot(values[:cmaxSamples.value], label=f"Channel {i}")

        self.ax.legend()
        self.canvas.draw()

        # Update output fields
        end_time = time.time()
        processing_time = (end_time - start_time) * 1000
        self.processing_time_label.setText(f"Average Processing Time: {processing_time:.2f} ms")
        self.frame_rate_label.setText(f"Average Frame Rate: {1 / (end_time - start_time):.2f} Hz")

        # Start next acquisition
        self.run_block_capture()

    def stop_measurement(self):
        if hasattr(self, 'c_handle'):
            self.status["stop"] = ps.ps4000aStop(self.c_handle)
            assert_pico_ok(self.status["stop"])
            self.status["close"] = ps.ps4000aCloseUnit(self.c_handle)
            assert_pico_ok(self.status["close"])
        self.timer.stop()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PicoScopeApp()
    window.show()
    sys.exit(app.exec())