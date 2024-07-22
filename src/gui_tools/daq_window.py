from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLineEdit, QLabel, QGridLayout,
                               QTabWidget, QFileDialog, QSplitter)
from PySide6.QtCore import Qt
import pyqtgraph as pg

class DAQWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DAQ Window")
        self.resize(1000, 600)

        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Top section
        top_layout = QHBoxLayout()
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.save_button = QPushButton("Save")
        self.save_path = QLineEdit()
        self.save_path.setPlaceholderText("Save path...")
        self.browse_button = QPushButton("Browse")

        top_layout.addWidget(self.start_button)
        top_layout.addWidget(self.stop_button)
        top_layout.addWidget(self.save_button)
        top_layout.addWidget(self.save_path)
        top_layout.addWidget(self.browse_button)

        # Connect buttons to functions
        self.start_button.clicked.connect(self.start_measurement)
        self.stop_button.clicked.connect(self.stop_measurement)
        self.save_button.clicked.connect(self.save_data)
        self.browse_button.clicked.connect(self.browse_save_path)

        # Main content layout with splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left section
        left_widget = QWidget()
        self.left_layout = QVBoxLayout()
        self.parameter_layout = QGridLayout()
        self.left_layout.addLayout(self.parameter_layout)
        self.left_layout.addStretch(1)  # This pushes everything to the top
        left_widget.setLayout(self.left_layout)
        splitter.addWidget(left_widget)

        # Right section
        self.tab_widget = QTabWidget()
        splitter.addWidget(self.tab_widget)

        # Set initial sizes for splitter
        splitter.setSizes([300, 700])  # Adjust these values as needed

        # Add layouts to main layout
        main_layout.addLayout(top_layout)
        main_layout.addWidget(splitter)

        # Setup parameter list and plots
        self.setup_parameter_list()
        self.setup_plots()

    def setup_parameter_list(self):
        # Implement this method in the subclass
        pass

    def setup_plots(self):
        # Implement this method in the subclass
        pass

    def start_measurement(self):
        # Implement this method in the subclass
        pass

    def stop_measurement(self):
        # Implement this method in the subclass
        pass

    def save_data(self):
        # Implement this method in the subclass
        pass

    def close_daq(self):
        # Implement this method in the subclass
        pass

    def browse_save_path(self):
        file_dialog = QFileDialog()
        save_path = file_dialog.getSaveFileName(self, "Save Data", "", "CSV Files (*.csv);;All Files (*)")[0]
        if save_path:
            self.save_path.setText(save_path)

    def add_parameter(self, name, default_value=""):
        row = self.parameter_layout.rowCount()
        self.parameter_layout.addWidget(QLabel(name), row, 0)
        line_edit = QLineEdit(default_value)
        # line_edit.setMaximumWidth(100)  # Set maximum width for input fields
        self.parameter_layout.addWidget(line_edit, row, 1)
        return line_edit

    def get_parameter_value(self, parameter_widget, value_type=str):
        return value_type(parameter_widget.text())

    def set_parameter_value(self, parameter_widget, value):
        parameter_widget.setText(str(value))

    def add_plot_tab(self, name):
        plot_widget = pg.PlotWidget()
        self.tab_widget.addTab(plot_widget, name)
        return plot_widget

    def closeEvent(self, event):
        self.close_daq()
        event.accept()

# Example usage:
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    class MyDAQWindow(DAQWindow):
        def setup_parameter_list(self):
            self.param1 = self.add_parameter("Parameter 1", "0")
            self.param2 = self.add_parameter("Parameter 2", "1.0")

        def setup_plots(self):
            self.plot1 = self.add_plot_tab("Plot 1")
            self.plot2 = self.add_plot_tab("Plot 2")

        def start_measurement(self):
            print("Starting measurement")
            print(f"Parameter 1: {self.get_parameter_value(self.param1, int)}")
            print(f"Parameter 2: {self.get_parameter_value(self.param2, float)}")

        def stop_measurement(self):
            print("Stopping measurement")

        def save_data(self):
            print(f"Saving data to: {self.save_path.text()}")

        def close_daq(self):
            print("Closing DAQ")

    app = QApplication(sys.argv)
    window = MyDAQWindow()
    window.show()
    sys.exit(app.exec())