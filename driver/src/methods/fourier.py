"""Provides methods related to the Fast Fourier Transform.

.. _src-methods-fourier:
    https://github.com/hivebattery/gui/blob/master/driver/src/methods/fourier.py

"""
from __future__ import division
from __future__ import absolute_import

import numpy as np


def get_impedance(data_set, n_samples):
    """Calculate Impedance.

    Calculates the real and imaginary impedance given arrays of current and voltage data.

    Args:
        data_set (list of float): A list made up of voltage and current data produced by the EIS.
        n_samples (int): The number of samples.

    Returns:
        list of complex: The real and imaginary impedance.

    """
    k = len(data_set) // 2
    periods = k // n_samples

    voltage = data_set[:k]
    current = data_set[k:]

    n = len(voltage) - n_samples

    fft_data_voltage = (np.fft.fft(voltage[n_samples:]) / n)[:(n // 2)]
    fft_data_current = (np.fft.fft(current[n_samples:]) / n)[:(n // 2)]

    fft_voltage = [fft_data_voltage[0]]
    fft_curr = [fft_data_current[0]]

    for i in range(1, len(fft_data_voltage)):
        fft_voltage.append(fft_data_voltage[i] * 2)
        fft_curr.append(fft_data_current[i] * 2)

    target_voltage = fft_voltage[periods - 1]
    target_current = fft_curr[periods - 1]

    mag = np.abs(target_voltage) / np.abs(target_current)
    angle = np.angle(target_voltage) - np.angle(target_current)

    return mag * np.cos(angle) + 1j * mag * np.sin(angle)
