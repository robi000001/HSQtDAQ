import numpy as np
from scipy import signal


def scale_array(x, a, b):
    # Convert x to float to avoid potential integer overflow
    x_float = x.astype(np.float64)

    result = x * a + b

    # Perform the calculation
    # result = np.multiply(a, x) + b

    # The result will automatically be a floating-point numpy array
    return result

x = np.array([1, 2, 3, 4, 5], dtype=np.int16)
a = 2.5  # floating point
b = 3.7  # floating point

result = scale_array(x, a, b)
print(result)  # Output: [ 6.2  8.7 11.2 13.7 16.2]
print(result.dtype)  # Output: float64