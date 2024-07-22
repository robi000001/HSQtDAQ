# DAQ window template

A simple template that could be used to create a GUI for a data acquisition system.
The template is a class that inherits from `QMainWindow` and contains the basic structure of a window with a top section,
a left section, and a right section.
The subclass should implement the folowing methods:

- `setup_parameter_list`: Creates the input fields to set the parameters of the data acquisition.
- `start_measurement`: Starts the data acquisition; called when the start button is pressed.
- `stop_measurement`: Stops the data acquisition; called when the stop button is pressed.
- `save_data`: Saves the data to a file; called when the save button is pressed.
- `close_daq`: Closes the data acquisition system; called when the exit button is pressed.


## Window structure

The window is divided into 3 main sections:

1. **Top section**: Contains the buttons to start and stop the measurement as well as tools to save data.
2. **Left section**: Contains the input fields to set the parameters of the data acquisition.
3. **Right section**: Contains the plot to display the data.

## Top section

The top section contains the following elements:

- **Start button**: Starts the data acquisition.
- **Stop button**: Stops the data acquisition.
- **Save button**: Saves the data to a file.
- **Save path**: Input field to set the path where the data will be saved.

## Left section

The left section contains several rows of labels and input fields to set the parameters of the data acquisition.
The template should have a function to create these rows dynamically based on the required parameters.
The template should also have a function to read or write the values from these input fields as text or numeric values (float or integer).

## Right section

The size of the right section should be adaptable to the size of the window.
The right section should contain multiple tabs to display different plots.
The template should have a function to create these tabs dynamically based on the number of plots required.

