import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLineEdit, \
    QLabel, QComboBox
from PySide6.QtCore import QTimer, Slot
import pyqtgraph as pg
import time
from src.common.utils import generate_composite_signal


class SimulationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DAQ Simulation")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.create_input_fields()
        self.create_buttons()
        self.create_plot()
        self.create_output_fields()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)

        self.is_running = False
        self.data = None
        self.time_axis = None
        self.current_index = 0
        self.start_time = time.time()
        self.iterations = 0

    def create_input_fields(self):
        input_layout = QHBoxLayout()
        self.sampling_freq_input = QLineEdit("10000")
        self.sampling_time_input = QLineEdit("10")
        self.update_rate_input = QLineEdit("10")
        self.num_channels_input = QLineEdit("16")
        self.channels_per_plot_input = QLineEdit("4")
        self.wave_type_input = QComboBox()
        self.wave_type_input.addItems(['sine', 'square', 'sawtooth', 'chirp'])

        input_layout.addWidget(QLabel("Sampling Freq (Hz):"))
        input_layout.addWidget(self.sampling_freq_input)
        input_layout.addWidget(QLabel("Sampling Time (s):"))
        input_layout.addWidget(self.sampling_time_input)
        input_layout.addWidget(QLabel("Update Rate (Hz):"))
        input_layout.addWidget(self.update_rate_input)
        input_layout.addWidget(QLabel("Num Channels:"))
        input_layout.addWidget(self.num_channels_input)
        input_layout.addWidget(QLabel("Channels per Plot:"))
        input_layout.addWidget(self.channels_per_plot_input)
        input_layout.addWidget(QLabel("Wave Type:"))
        input_layout.addWidget(self.wave_type_input)

        self.layout.addLayout(input_layout)

    def create_buttons(self):
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.exit_button = QPushButton("Exit")

        self.start_button.clicked.connect(self.start_simulation)
        self.stop_button.clicked.connect(self.stop_simulation)
        self.exit_button.clicked.connect(self.close)

        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.exit_button)

        self.layout.addLayout(button_layout)

    def create_plot(self):
        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)

    def create_output_fields(self):
        output_layout = QHBoxLayout()
        self.frame_rate_label = QLabel("Frame Rate: 0 Hz")
        self.processing_time_label = QLabel("Processing Time: 0 ms")

        output_layout.addWidget(self.frame_rate_label)
        output_layout.addWidget(self.processing_time_label)

        self.layout.addLayout(output_layout)

    @Slot()
    def start_simulation(self):
        if not self.is_running:
            self.is_running = True
            self.sampling_freq = int(self.sampling_freq_input.text())
            self.sampling_time = int(self.sampling_time_input.text())
            self.update_rate = int(self.update_rate_input.text())
            self.num_channels = int(self.num_channels_input.text())
            self.channels_per_plot = int(self.channels_per_plot_input.text())
            self.wave_type = self.wave_type_input.currentText()

            self.data = generate_composite_signal(self.sampling_freq, self.sampling_time, self.num_channels,
                                                  self.wave_type)
            self.time_axis = np.linspace(0, self.sampling_time, self.sampling_freq * self.sampling_time, endpoint=False)
            self.current_index = 0

            self.plot_widget.clear()
            self.curves = []
            colors = ['r', 'g', 'b', 'c', 'm', 'y', 'w']
            for i in range(self.num_channels):
                color = colors[i % len(colors)]
                curve = self.plot_widget.plot(pen=color)
                self.curves.append(curve)

            self.timer.start(1000 // self.update_rate)
        self.start_time = time.time()
        self.iterations = 0

    @Slot()
    def stop_simulation(self):
        self.is_running = False
        self.timer.stop()

    @Slot()
    def update_plot(self):
        if self.is_running:
            start_time = time.time()


            end_index = min(self.current_index + self.sampling_freq // self.update_rate, len(self.time_axis))
            x = self.time_axis[self.current_index:end_index]

            for i, curve in enumerate(self.curves):
                y = self.data[i][self.current_index:end_index]
                curve.setData(x, y)

            self.current_index = end_index
            if self.current_index >= len(self.time_axis):
                self.current_index = 0

            processing_time = (time.time() - start_time) * 1000
            total_time = (time.time() - self.start_time) * 1000
            average_time = total_time / (self.iterations + 1)
            self.iterations += 1

            self.processing_time_label.setText(f"Average time: {average_time:.2f} ms")
            self.frame_rate_label.setText(f"Iteration: {self.iterations}")
            # self.frame_rate_label.setText(f"Frame Rate: {1000 / update_time:.2f} Hz")


def main():
    app = QApplication([])
    window = SimulationWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()