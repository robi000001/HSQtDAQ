import numpy as np
from scipy import signal
from typing import Union, overload


@overload
def scale_adc_two_complement(input_data: int, bit_resolution: int, voltage_range: float) -> float:
    ...


@overload
def scale_adc_two_complement(input_data: np.ndarray, bit_resolution: int, voltage_range: float) -> np.ndarray:
    ...


def scale_adc_two_complement(
    input_data: Union[int, np.ndarray],
    bit_resolution: int,
    voltage_range: float
) -> Union[float, np.ndarray]:
    """Scale ADC data from two's complement to voltage.

    :param input_data: Input data in two's complement format (skalars or numpy array)
    :param bit_resolution: Bit resolution of the ADC
    :param voltage_range: Voltage range of the ADC
    :return: Scaled data in volts
    """
    # Calculate the scaling factor
    scaling_factor = voltage_range / (2 ** (bit_resolution - 1))  # range / 2^(n-1), no need to subtract 1!
    # Scale the data
    return input_data * scaling_factor



def generate_waves(sampling_freq, sampling_time, num_channels, wave_type='sine'):
    """
    Generate sample waves for multiple channels.

    :param sampling_freq: Sampling frequency in Hz
    :param sampling_time: Total sampling time in seconds
    :param num_channels: Number of channels to generate
    :param wave_type: Type of wave to generate ('sine', 'square', 'sawtooth', or 'chirp')
    :return: numpy array of shape (num_channels, num_samples)
    """
    num_samples = int(sampling_freq * sampling_time)
    t = np.linspace(0, sampling_time, num_samples, endpoint=False)

    # Create a meshgrid for vectorized operations
    channel_indices = np.arange(num_channels)[:, np.newaxis]
    t_mesh, channel_mesh = np.meshgrid(t, channel_indices)

    # Calculate frequencies and amplitudes for each channel
    frequencies = 1 + channel_mesh * 0.5
    amplitudes = 1 + channel_mesh * 0.2
    phases = channel_mesh * np.pi / 8

    if wave_type == 'sine':
        waves = amplitudes * np.sin(2 * np.pi * frequencies * t_mesh + phases)
    elif wave_type == 'square':
        waves = amplitudes * signal.square(2 * np.pi * frequencies * t_mesh + phases)
    elif wave_type == 'sawtooth':
        waves = amplitudes * signal.sawtooth(2 * np.pi * frequencies * t_mesh + phases)
    elif wave_type == 'chirp':
        # For chirp, we'll use a different frequency range for each channel
        f0 = 1 + channel_mesh  # Start frequency
        f1 = 10 + channel_mesh * 2  # End frequency
        waves = amplitudes * signal.chirp(t_mesh, f0, sampling_time, f1)
    else:
        raise ValueError("Invalid wave type. Choose 'sine', 'square', 'sawtooth', or 'chirp'.")

    return waves


def generate_random_noise(sampling_freq, sampling_time, num_channels, scale=0.1):
    """
    Generate random noise for multiple channels.

    :param sampling_freq: Sampling frequency in Hz
    :param sampling_time: Total sampling time in seconds
    :param num_channels: Number of channels to generate
    :param scale: Scale of the noise (standard deviation)
    :return: numpy array of shape (num_channels, num_samples)
    """
    num_samples = int(sampling_freq * sampling_time)
    return np.random.normal(0, scale, (num_channels, num_samples))


def generate_composite_signal(sampling_freq, sampling_time, num_channels, wave_type='sine', noise_scale=0.1):
    """
    Generate a composite signal of waves and random noise.

    :param sampling_freq: Sampling frequency in Hz
    :param sampling_time: Total sampling time in seconds
    :param num_channels: Number of channels to generate
    :param wave_type: Type of wave to generate ('sine', 'square', 'sawtooth', or 'chirp')
    :param noise_scale: Scale of the noise to add
    :return: numpy array of shape (num_channels, num_samples)
    """
    waves = generate_waves(sampling_freq, sampling_time, num_channels, wave_type)
    noise = generate_random_noise(sampling_freq, sampling_time, num_channels, noise_scale)
    return waves + noise


def calculate_rms(data):
    """Calculate the Root Mean Square (RMS) of the input data."""
    return np.sqrt(np.mean(np.square(data)))

def calculate_fft(data, sampling_freq):
    """Calculate the Fast Fourier Transform (FFT) of the input data."""
    fft_result = np.fft.fft(data)
    freqs = np.fft.fftfreq(len(data), 1/sampling_freq)
    return freqs, np.abs(fft_result)

def calculate_snr(signal, noise):
    """Calculate the Signal-to-Noise Ratio (SNR) in dB."""
    signal_power = np.mean(np.square(signal))
    noise_power = np.mean(np.square(noise))
    return 10 * np.log10(signal_power / noise_power)