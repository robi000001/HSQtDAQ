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
        self.setWindowTitle("PicoScope Measurement")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.create_input_fields()
        self.create_buttons()
        self.create_plot()
        self.create_output_fields()

        self.chandle = ctypes.c_int16()
        self.status = {}
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_measurement)

    def create_input_fields(self):
        input_layout = QHBoxLayout()
        self.sampling_freq = QLineEdit("1000000")
        self.sampling_time = QLineEdit("1")
        self.num_channels = QLineEdit("4")
        input_layout.addWidget(QLabel("Sampling Frequency (Hz):"))
        input_layout.addWidget(self.sampling_freq)
        input_layout.addWidget(QLabel("Sampling Time (s):"))
        input_layout.addWidget(self.sampling_time)
        input_layout.addWidget(QLabel("Number of Channels:"))
        input_layout.addWidget(self.num_channels)
        self.layout.addLayout(input_layout)

    def create_buttons(self):
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.exit_button = QPushButton("Exit")
        self.start_button.clicked.connect(self.start_measurement)
        self.stop_button.clicked.connect(self.stop_measurement)
        self.exit_button.clicked.connect(self.close)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.exit_button)
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

    def start_measurement(self):
        try:
            # Open PicoScope
            self.status["openunit"] = ps.ps4000aOpenUnit(ctypes.byref(self.chandle), None)
            assert_pico_ok(self.status["openunit"])

            # Configure channels
            num_channels = int(self.num_channels.text())
            channel_range = 7  # PS4000A_2V
            for i in range(num_channels):
                channel = i  # Use channel number directly
                self.status[f"setChA{i}"] = ps.ps4000aSetChannel(
                    self.chandle,
                    channel,
                    1,  # enabled
                    1,  # dc coupled
                    channel_range,
                    0.0  # analogue offset
                )
                assert_pico_ok(self.status[f"setChA{i}"])

            # Set up data buffers
            sampling_freq = int(self.sampling_freq.text())
            sampling_time = float(self.sampling_time.text())
            self.num_samples = int(sampling_freq * sampling_time)
            self.max_adc = ctypes.c_int16()
            self.status["maximumValue"] = ps.ps4000aMaximumValue(self.chandle, ctypes.byref(self.max_adc))
            assert_pico_ok(self.status["maximumValue"])

            self.buffers = [np.zeros(self.num_samples, dtype=np.int16) for _ in range(num_channels)]
            for i, buffer in enumerate(self.buffers):
                self.status[f"setDataBufferA{i}"] = ps.ps4000aSetDataBuffer(
                    self.chandle,
                    i,  # channel
                    buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                    self.num_samples,
                    0,  # segment index
                    0  # ratio mode
                )
                assert_pico_ok(self.status[f"setDataBufferA{i}"])

            # Configure streaming
            # Ensure sample interval is at least 1 µs (1000 ns)
            sample_interval_ns = max(1000, int(1e9 / sampling_freq))
            sampleInterval = ctypes.c_uint32(sample_interval_ns)
            sampleIntervalTimeUnits = ps.PS4000A_TIME_UNITS['PS4000A_NS']
            maxPreTriggerSamples = ctypes.c_uint32(0)
            maxPostTriggerSamples = ctypes.c_uint32(self.num_samples)
            autoStop = ctypes.c_int16(1)
            downSampleRatio = ctypes.c_uint32(1)
            downSampleRatioMode = ps.PS4000A_RATIO_MODE['PS4000A_RATIO_MODE_NONE']
            overviewBufferSize = ctypes.c_uint32(self.num_samples)

            self.status["runStreaming"] = ps.ps4000aRunStreaming(
                self.chandle,
                ctypes.byref(sampleInterval),
                sampleIntervalTimeUnits,
                maxPreTriggerSamples,
                maxPostTriggerSamples,
                autoStop,
                downSampleRatio,
                downSampleRatioMode,
                overviewBufferSize
            )
            assert_pico_ok(self.status["runStreaming"])

            self.timer.start(50)  # Update every 50 ms

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            self.stop_measurement()

    def update_measurement(self):
        start_time = time.time()

        # Collect data from PicoScope
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        self.status["getStreamingLatestValues"] = ps.ps4000aGetStreamingLatestValues(
            self.chandle,
            None,
            ctypes.byref(ready)
        )

        if ready.value == 1:
            # Data is ready, process it
            for i, buffer in enumerate(self.buffers):
                self.status[f"getValues{i}"] = ps.ps4000aSetDataBuffer(
                    self.chandle,
                    i,
                    buffer.ctypes.data_as(ctypes.POINTER(ctypes.c_int16)),
                    self.num_samples,
                    0,
                    0
                )
                assert_pico_ok(self.status[f"getValues{i}"])

            overflow = ctypes.c_int16()
            cmaxSamples = ctypes.c_uint32(self.num_samples)
            self.status["getValues"] = ps.ps4000aGetValues(
                self.chandle,
                0,
                ctypes.byref(cmaxSamples),
                0,
                0,
                0,
                ctypes.byref(overflow)
            )
            assert_pico_ok(self.status["getValues"])

            # Process and update plot
            self.ax.clear()
            for i, buffer in enumerate(self.buffers):
                # Convert ADC counts to millivolts
                max_adc = self.max_adc.value
                channel_range = 7  # PS4000A_2V
                values = adc2mV(buffer, channel_range, max_adc)
                self.ax.plot(values[:cmaxSamples.value], label=f"Channel {i}")

            self.ax.legend()
            self.canvas.draw()

            # Update output fields
            end_time = time.time()
            processing_time = (end_time - start_time) * 1000
            self.processing_time_label.setText(f"Average Processing Time: {processing_time:.2f} ms")
            self.frame_rate_label.setText(f"Average Frame Rate: {1 / (end_time - start_time):.2f} Hz")

    def stop_measurement(self):
        if hasattr(self, 'chandle'):
            self.status["stop"] = ps.ps4000aStop(self.chandle)
            assert_pico_ok(self.status["stop"])
            self.status["close"] = ps.ps4000aCloseUnit(self.chandle)
            assert_pico_ok(self.status["close"])
        self.timer.stop()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PicoScopeApp()
    window.show()
    sys.exit(app.exec())