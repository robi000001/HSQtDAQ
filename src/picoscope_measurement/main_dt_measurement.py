from typing import override
import numpy as np
import time
from src.picoscope_measurement.main_pico import PicoScopeApp


class PicoDtApp(PicoScopeApp):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PicoScope time delay measurement")

        self.threshold_ui = self.add_parameter("Threshold [V]", 0.5)
        self.canvas_proc, self.figure_proc, self.ax_proc = self.add_pyplot_tab("Delays")

        # Initialize data storage for time differences
        self.start_time = None
        self.measurement_times = None
        self.time_differences = None

    def start_measurement(self):
        super().start_measurement()
        self.start_time = time.time()
        self.measurement_times = []
        self.time_differences = [[] for _ in range(self.num_channels - 1)]

    def find_rising_edge_crossing(self, x_data, y_data, threshold):
        # Find where the signal is below the threshold
        below_threshold = y_data < threshold
        # Find where the signal transitions from below to above threshold
        rising_edges = np.where(np.diff(below_threshold.astype(int)) == -1)[0]

        if len(rising_edges) > 0:
            # Return the time of the first rising edge crossing
            return x_data[rising_edges[0] + 1]
        else:
            print("No rising edge crossing found")
            return None

    @override
    def process_data(self, x_data: np.ndarray, y_data: list[np.ndarray]) -> None:
        """
        Process the acquired data to find threshold crossings and calculate time differences.

        Args:
            x_data (np.ndarray): The time axis data.
            y_data (list[np.ndarray]): List of voltage data for each channel.

        Returns:
            None: This method updates the internal state and plot but does not return a value.
        """
        # print("Processing data")

        threshold = self.get_float_parameter_value(self.threshold_ui)

        # Find the first rising edge threshold crossing for each channel
        crossing_times = []
        for channel_data in y_data:
            crossing_time = self.find_rising_edge_crossing(x_data, channel_data, threshold)
            crossing_times.append(crossing_time)

        # Calculate time differences relative to the first channel
        reference_time = crossing_times[0]
        current_time_differences = []
        for crossing_time in crossing_times[1:]:
            if crossing_time is not None and reference_time is not None:
                current_time_differences.append(crossing_time - reference_time)
            else:
                current_time_differences.append(None)

        # Update the time differences storage
        if self.start_time is None:
            self.start_time = time.time()

        current_measurement_time = time.time() - self.start_time
        self.measurement_times.append(current_measurement_time)

        for i, diff in enumerate(current_time_differences):
            self.time_differences[i].append(diff)

        # Update the delay plot
        self.ax_proc.clear()

        for i, diffs in enumerate(self.time_differences):
            valid_times = [t for t, d in zip(self.measurement_times, diffs) if d is not None]
            valid_diffs = [d for d in diffs if d is not None]
            if valid_diffs:
                self.ax_proc.plot(valid_times, valid_diffs, label=f'Channel {i + 2}')

        self.ax_proc.set_xlabel("Measurement Time (s)")
        self.ax_proc.set_ylabel("Time Delay (s)")
        self.ax_proc.set_title("Time Delays Relative to Channel 1 Over Time")
        self.ax_proc.legend()

        # Limit the number of points to display (e.g., last 100 points)
        # max_points = 100
        # if len(self.measurement_times) > max_points:
        #     self.ax_proc.set_xlim(self.measurement_times[-max_points], self.measurement_times[-1])

        self.canvas_proc.draw()

    def save_data(self):
        file_path = self.save_path.text()
        if not file_path:
            print("No save path specified.")
            return

        try:
            # Save processed time delay data
            processed_data = np.column_stack([self.measurement_times] + self.time_differences)
            np.savetxt(file_path, processed_data, delimiter=',',
                       header='Measurement_Time,' + ','.join(f'Delay_Ch{i+2}' for i in range(len(self.time_differences))))

            # Save time delay graph
            self.figure_proc.savefig(f"{file_path}_delay_graph.png", dpi=300, bbox_inches='tight')

            print(f"Data and graph saved to {file_path}")
        except Exception as e:
            print(f"Error saving data: {e}")


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = PicoDtApp()
    window.show()
    app.exec()