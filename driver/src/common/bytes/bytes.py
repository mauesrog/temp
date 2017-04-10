"""Bitwise operations.

Provides certain helper functions to perform operations on bytearrays and other data types.

Todo:
    * Get rid of src.common.linear_algebra altogether.

.. _src-common-bytes:
    https://github.com/hivebattery/gui/blob/master/driver/src/common/bytes/bytes.py

"""
from __future__ import division
from __future__ import absolute_import
import re
import numpy as np

from src.common.linear_algebra import matrix

TRAILING_ZERO_BITS_RIGHT = [32, 0, 1, 26, 2, 23, 27, 0, 3, 16, 24, 30, 28, 11, 0, 13, 4, 7, 17, 0, 25, 22, 31, 15, 29,
                            10, 12, 6, 0, 21, 14, 9, 5, 20, 8, 19, 18]
"""list of int: Provides a way to calculate the number of trailing zero bits to the right in constant time. Given a
bitstring `byte`,

Example:
::
    TRAILING_ZERO_BITS_RIGHT[(-int(byte, 2) & int(byte, 2)) % 37]
"""


def byte_to_double(byte_arr, scale, n_bits):
    """Convert byte to double.

    Assuming IEEE 754-2008 single-precision float encoding, takes a byte as its input and returns a double.

    Args:
        byte_arr (list): The list of bits to be converted
        scale (int): The number of possible digits in each byte
        n_bits (int): The number of bits to be converted.

    Returns:
        float: The double converted from the byte.

    """
    bytes_arr = list(reversed(byte_arr))
    bytes_arr = list(map(lambda x: bin(int(x, scale))[2:].zfill(n_bits), bytes_arr))
    sign = int(bytes_arr[0][0], 2)
    exp = int("".join(bytes_arr[0][1:8] + bytes_arr[1][0]), 2)
    mantissa = 1.0
    mantissa_arr = list(map(int, bytes_arr[1][1:] + bytes_arr[2] + bytes_arr[3]))

    for j in range(len(mantissa_arr)):
        mantissa += mantissa_arr[j] * 2**(-(j+1))

    return (-1)**sign * 2**(exp - 127) * mantissa


def bytes_to_double(arr):
    """Converts bytearrays to an array of doubles.

    Args:
        arr (bytearray): Contains all bytes that will be converted to doubles.

    Returns:
        list of double: The array of doubles.

    """
    i = 0
    bytes_arr = None
    doubles = []

    for bit in arr:
        i %= 4

        if i == 0:
            if bytes_arr is not None:
                doubles.append(byte_to_double(bytes_arr, 16, 8))

            bytes_arr = []

        bytes_arr.append("%02X" % bit)
        i += 1

    if bytes_arr is not None:
        doubles.append(byte_to_double(bytes_arr, 16, 8))

    return doubles


def get_num_middle_bits(a, b, f=1.0):
    """Get the number of bits between two numbers.

    It doesn't matter if `a` and `b` are integers because this operation takes the floor of the lower bound and the
    floor of the upper bound.

    Note:
        Since this method uses logarithms to calculate the number of middle bits, it runs in constant time.

    Args:
        a (float): The first number (the lower bound).
        b (float): The second number (the upper bound).
        f (float, optional): Any factor by which `a` and `b` were previously multiplied. Default is no factor i.e.
            1.0.

    Returns:
        int: The number of bits between the lower and upper bounds.

    """
    x, y = get_binary_limits(a, b, f)

    return int(y - x - 1)


def get_binary_limits(a, b, f=1.0):
    """Get the power of two closest to two numbers.

    We want the power of 2 closest to the floor of the lower bound and the one closest to the ceiling of the upper
    bound. Any factor by which the two numbers where previously multiplied gets divided out before any calculations.

    Args:
        a (float): The first number (the lower bound).
        b (float): The second number (the upper bound).
        f (float, optional): Any factor by which `a` and `b` were previously multiplied. Default is no factor i.e.
            1.0.

    Returns:
        (int, int): The two powers of 2.

    """
    x = np.floor(np.log2(a / f))
    y = np.ceil(np.log2(b / f))

    return int(x), int(y)


def get_num_chained_zero_bits(left, right):
    """Get the length of the largest chain of zeroes between two binary strings.

    Given two binary strings, check how many zeroes can be chained when the two string are put together.

    Example:
        The binary strings '101000100' and '0000100' would return 6, because the concatenated string
        '1010001000000100' contains a chain of 6 zeroes between the two strings.

    Args:
        left (str): The binary string to be concatenated from the left. In our example, `left = '101000100'`.
        right (str): The binary string to be concatenated from the right. In our example, `right = '0000100'`

    Returns:
        int: The number of zeroes in the largest bewteen the two binary strings. In our example, 6.

    """
    if int(left[-1], 10) == 0:
        if int(left, 2) == 0:
            m = len(left)
        else:
            m = TRAILING_ZERO_BITS_RIGHT[(-int(left, 2) & int(left, 2)) % 37]
    else:
        m = 0

    if int(right[0], 10) == 0:
        if int(right, 2) == 0:
            n = len(right)
        else:
            n = TRAILING_ZERO_BITS_RIGHT[(-int(right[::-1], 2) & int(right[::-1], 2)) % 37]
    else:
        n = 0

    return m, n


def balance_binary_string(a, b, n_bits, f=1.0):
    """Evenly distribute ones between two powers of two.

    Given two numbers that don't necessarily need to be integers, distribute the specified number of 1's amongst the
    powers of 2 between the two numbers.

    Example:
        If `a = 2`, `b = 8192`, `f = 2`, and `n_bits = 3`, then this method would distribute three 1's across the powers
        of 2 between 0 and 12 i.e. '1001001001001'.

    Args:
        a (float): The lower bound.
        b (float): The upper bound.
        n_bits (int): The number of bits to be evenly distributed.
        f (float, optional): Any factor by which `a` and `b` were previously multiplied. Default is no factor i.e.
            1.0.

    Returns:
        str: The binary string with the 1's evenly distributed across the powers of 2 between the bounds.

    """
    middle_bits = "1"
    n_middle_bits = get_num_middle_bits(a, b, f)

    if n_bits > 0:
        middle_bits += distribute_bits(n_bits, n_middle_bits)
    else:
        for i in range(n_middle_bits):
            middle_bits += "0"

    return middle_bits + "1"


def map_ones_to_decimal(byte, factor=1.0):
    """Map a binary string to a list of decimals.

    Example:
        If the minimum frequency is 3,72529, then '1001' would return `[3.72529, 29.80232]`.

    Args:
        byte (str): The binary string.
        factor (float, optional): The minimum frequency.

    Returns:
        list of float: The frequencies encoded by the binary string.

    """
    offset = TRAILING_ZERO_BITS_RIGHT[(-int(byte, 2) & int(byte, 2)) % 37]

    n = 1 << offset
    nums = []

    for i in range(len(byte) - offset):
        if n & int(byte, 2):
            nums.append(str(n * factor))

        n <<= 1

    return nums


def distribute_bits(bits, max_bits):
    """Evenly distribute ones between two powers of two, without including the bounds.

    Given two numbers that don't necessarily need to be integers, distribute the specified number of 1's amongst the
    powers of 2 between the two numbers. This method takes care of the middle bits, and excludes the bounds.

    Args:
        bits (int): The number of 1's to distribute.
        max_bits (int): The length of the binary string where the 1's will be distributed.

    Returns:
        str: The binary string with 1's distributed.

    """
    n_bits = bits if max_bits > bits * 2 else max_bits - bits

    if n_bits == 0:
        curr_bit = "0" if max_bits > bits * 2 else "1"
        return "".join([curr_bit for i in range(max_bits)])

    N = matrix.Matrix(n_bits + 1, max_bits + 1)
    E = matrix.Matrix(n_bits + 1, max_bits + 1)

    for i in range(n_bits + 1):
        for j in range(max_bits + 1):
            e = ""
            if i == 0:
                n = j**3
                e += bin(0)[2:].zfill(j)

            elif j == 0:
                n = 0
                e += "1"
            else:
                n = -1

            N.set_value(i, j, n)
            E.set_value(i, j, e)

    N.set_value(1, 1, 0)
    E.set_value(1, 1, "1")

    for i in range(1, n_bits + 1):
        for k in range(i, max_bits + 1):
            if i == 1 and k == 1:
                continue

            q = float("inf")
            q_e = ""

            for j in range(1, k):
                for l in range(1, i + 1):
                    first_half = N.get_value(l, j)
                    second_half = N.get_value(i - l, k - j)

                    val = first_half + second_half

                    if val < q:
                        left = E.get_value(l, j)
                        right = E.get_value(i - l, k - j)

                        reps = 0
                        while reps < 4 and int(left[-1], 10) == 0 and int(right[0], 10) == 0:
                            if reps % 2 == 1:
                                right = right[::-1]

                            left = left[::-1]
                            reps += 1

                        if int(left[-1], 10) == 0 and int(right[0], 10) == 0:
                            le = left
                            r = right

                            init_val = val
                            min_val = float("inf")

                            for x in range(4):
                                m, n = get_num_chained_zero_bits(le, r)
                                v = init_val - m ** 3 - n ** 3 + (m + n) ** 3

                                if v < min_val:
                                    min_val = v
                                    left = le
                                    right = r

                                if x % 2 == 1:
                                    r = r[::-1]

                                le = le[::-1]

                            val = min_val

                        if val < q:
                            q = val
                            q_e = left + right

            N.set_value(i, k, q)
            E.set_value(i, k, q_e)

    distribution = E.get_value(n_bits, max_bits)

    return distribution if max_bits > 2 * bits \
        else re.sub(u'#', u'0', re.sub(u'0', u'1', re.sub(u'1', u'#', distribution)))