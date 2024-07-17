import sys
import time
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLineEdit, QLabel
from PySide6.QtCore import QTimer, Signal, Slot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import nidaqmx
from nidaqmx.constants import TerminalConfiguration, AcquisitionType

class DAQMeasurement(QMainWindow):
    data_ready = Signal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("NI DAQ Measurement")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.create_input_fields()
        self.create_buttons()
        self.create_plot()
        self.create_output_fields()

        self.task = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_acquisition_status)

        self.start_time = None
        self.cycle_count = 0
        self.total_processing_time = 0

        self.data_ready.connect(self.process_data)
        self.all_data = None
        self.is_running = False

    def create_input_fields(self):
        input_layout = QHBoxLayout()
        self.device_name_input = QLineEdit("Dev1")
        self.sampling_freq_input = QLineEdit("10000")
        self.sampling_time_input = QLineEdit("1")
        self.num_channels_input = QLineEdit("1")
        self.voltage_range_input = QLineEdit("10")

        input_layout.addWidget(QLabel("Device Name:"))
        input_layout.addWidget(self.device_name_input)
        input_layout.addWidget(QLabel("Sampling Frequency (Hz):"))
        input_layout.addWidget(self.sampling_freq_input)
        input_layout.addWidget(QLabel("Sampling Time (s):"))
        input_layout.addWidget(self.sampling_time_input)
        input_layout.addWidget(QLabel("Number of Channels:"))
        input_layout.addWidget(self.num_channels_input)
        input_layout.addWidget(QLabel("Voltage Range (V):"))
        input_layout.addWidget(self.voltage_range_input)

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
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.layout.addWidget(self.canvas)

    def create_output_fields(self):
        output_layout = QHBoxLayout()
        self.cycle_rate_label = QLabel("Average Cycle Rate: 0 Hz")
        self.processing_time_label = QLabel("Average Processing Time: 0 ms")

        output_layout.addWidget(self.cycle_rate_label)
        output_layout.addWidget(self.processing_time_label)

        self.layout.addLayout(output_layout)

    def start_measurement(self):
        if not self.is_running:
            self.is_running = True
            self.start_time = time.time()
            self.cycle_count = 0
            self.total_processing_time = 0
            self.start_acquisition_cycle()

    def start_acquisition_cycle(self):
        try:
            device_name = self.device_name_input.text()
            sampling_freq = float(self.sampling_freq_input.text())
            sampling_time = float(self.sampling_time_input.text())
            num_channels = int(self.num_channels_input.text())
            voltage_range = float(self.voltage_range_input.text())

            if num_channels < 1 or num_channels > 16:
                raise ValueError("Number of channels must be between 1 and 16")

            self.task = nidaqmx.Task()
            for i in range(num_channels):
                self.task.ai_channels.add_ai_voltage_chan(f"{device_name}/ai{i}",
                                                          terminal_config=TerminalConfiguration.RSE,
                                                          min_val=-voltage_range, max_val=voltage_range)

            samples_per_channel = int(sampling_freq * sampling_time)
            self.task.timing.cfg_samp_clk_timing(sampling_freq, sample_mode=AcquisitionType.FINITE,
                                                 samps_per_chan=samples_per_channel)

            self.all_data = np.zeros((num_channels, samples_per_channel))

            self.task.start()
            self.timer.start(50)  # Check acquisition status every 50 ms

        except Exception as e:
            print(f"Error starting measurement: {e}")
            self.is_running = False

    def stop_measurement(self):
        self.is_running = False
        if self.task:
            self.task.stop()
            self.task.close()
            self.task = None
        self.timer.stop()

    def check_acquisition_status(self):
        if self.task and self.task.is_task_done():
            self.timer.stop()
            self.read_and_process_data()

    def read_and_process_data(self):
        try:
            data = self.task.read(number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE)
            self.task.stop()
            self.task.close()
            self.task = None

            if data and len(data) > 0:
                data_array = np.array(data)
                if data_array.size > 0:
                    self.data_ready.emit(data_array)
            else:
                print("No data available")

        except nidaqmx.errors.DaqError as e:
            print(f"Error reading data: {e}")
            self.stop_measurement()

    @Slot(np.ndarray)
    def process_data(self, data):
        start_time = time.time()

        if data.size == 0:
            print("Received empty data")
            return

        if len(data.shape) == 1:
            data = data.reshape(1, -1)

        num_channels, samples_per_channel = data.shape
        self.all_data = data

        self.ax.clear()
        time_array = np.linspace(0, samples_per_channel / float(self.sampling_freq_input.text()), samples_per_channel)

        for i in range(num_channels):
            self.ax.plot(time_array, self.all_data[i], label=f"Channel {i+1}")

        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Voltage (V)")
        self.ax.legend()
        self.canvas.draw()

        processing_time = (time.time() - start_time) * 1000  # Convert to ms
        self.total_processing_time += processing_time
        self.cycle_count += 1

        elapsed_time = time.time() - self.start_time
        avg_cycle_rate = self.cycle_count / elapsed_time
        avg_processing_time = self.total_processing_time / self.cycle_count

        self.cycle_rate_label.setText(f"Average Cycle Rate: {avg_cycle_rate:.2f} Hz")
        self.processing_time_label.setText(f"Average Processing Time: {avg_processing_time:.2f} ms")

        if self.is_running:
            self.start_acquisition_cycle()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DAQMeasurement()
    window.show()
    sys.exit(app.exec())