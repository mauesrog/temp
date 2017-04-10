"""Console logging utilities.

These operations works with the `Console` component.

.. _src-common-log-console_message:
    https://github.com/hivebattery/gui/blob/master/driver/src/common/log/console_message.py

"""
from __future__ import absolute_import

import datetime

from src.config.config import *
from src.common.file import format as format_file

CHAR_LENGTH = 2
"""int: The length of each character printed to the console.
"""
MESSAGE_FORMATS = ["%s", "%s value %i out of bounds. Acceptable values fall between %f and %f, inclusive.",
                   "'%s' is not an %s.", "%s, %i, is larger than %s, %i.", "Device disconnected.",
                   "Endpoints couldn't be established", "Error writing to device", "Still processing previous request!",
                   "Wrong number of bytes.", "Error fetching error code from device.",
                   "Error determining which frequency to run next.",
                   "Couldn't write battery voltage as a float (didn't get 4 bytes back)",
                   "Error saving %s as default path. Go to 'File' > 'Change default csv path...' to set a default "
                   "path.", "Unknown usb error occurred when trying to %s."]
"""list of str: Defines what each message code should log, where the index into this list corresponds to the code.
"""
BACKEND_MESSAGES = ["Battery voltage range (2V-5V) violated, check battery connections", "Timeout Error -- Precharge",
                    "Timeout Error -- Buck Converter Bringup", "Detected impedance below minimum",
                    "Detected impedance above maximum", "Error - Controller Shutdown", "Timeout Error -- Servo Loop",
                    "Timeout Error -- Z Test", "Timeout Error -- Setup", "Timeout Error -- Run",
                    "Timeout Error -- Send"]
"""list of str: Defines what each backend message code returned from the device should log, where the index into this
list corresponds to the second byte of the code.
"""

ACTION_CANCELED = -3
"""int: Code for a cancelled action.
"""
ACTION_REQUIRED_MSG = -2
"""int: Code for an action that requires the user to do something.
"""
REQUEST_MSG = -1
"""int: Code to indicate a request just fired.
"""
SUCCESS_MSG = 0
"""int: Code to indicate the success of some operation.
"""

ERR_OUT_OF_BOUNDS = 1
"""int: Error when the user inputs values out of the bounds defined by some particular entry in the form.
"""
ERR_TYPE = 2
"""int: Error when the user inputs something other than the required data type for some entry.
"""
ERR_WRONG_LIMITS = 3
"""int: Error when the lower limit is greater than the upper limit.
"""
ERR_USB_DEVICE_NOT_FOUND = 4
"""int: Error when the device cannot be found or when the device is disconnected.
"""
ERR_USB_ENDPOINTS = 5
"""int: Error when the reference to some USB endpoint of the device fails to be produced.
"""
ERR_USB_WRITE = 6
"""int: Error when some data wasn't successfully written to a register in the device.
"""
ERR_USB_ONGOING_EIS = 7
"""int: Error that occurs during an ongoing data transfer.
"""
ERR_USB_WRONG_NUM_BYTES = 8
"""int: Error when the device detects less or more bytes than it expected.
"""
ERR_USB_READ_ERROR_CODE = 9
"""int: Error when reading a register is impossible or results in faulty data with the wrong number of bytes.
"""
ERR_USB_NO_FREQ_SPEC = 10
"""int: Error when the device does not receive the frequency id with the start EIS request.
"""
ERR_USB_WRITE_BATT_VOLTAGE = 11
"""int: Error when the device couldn't send back the battery voltage to the computer.
"""
ERR_WRITE_DEFAULT_PATH = 12
"""int: Error when the path of the directory where the csv files are saved could not be updated.
"""
ERR_USB_OTHER = 13
"""int: Error when some other USB related error happened.
"""

LATEST_ERRORS_START_FREQ = 0
"""int: The index of the latest error related to the start frequency.
"""
LATEST_ERRORS_END_FREQ = 1
"""int: The index of the latest error related to the end frequency.
"""
LATEST_ERRORS_RANGE = 2
"""int: The index of the latest error related to discordant lower and upper bounds.
"""
LATEST_ERRORS_AMPLITUDE = 3
"""int: The index of the latest error related to the amplitude.
"""
LATEST_ERRORS_DEVICE_NOT_FOUND = ERR_USB_DEVICE_NOT_FOUND
"""int: The index of the latest error related to device disconnection.
"""
LATEST_ERRORS_USB_ENDPOINTS = ERR_USB_ENDPOINTS
"""int: The index of the latest error related to USE endpoints.
"""
LATEST_ERRORS_USB_WRITE = ERR_USB_WRITE
"""int: The index of the latest error related to writing to a register via USB.
"""

#: Errors related to the EIS controller
ERR_SERVO = 0xF0
ERR_TIMEOUT_PRECHARGE = 0xF1
ERR_TIMEOUT_BUCKUP = 0xF2
ERR_ZTEST_LOW = 0xF3
ERR_ZTEST_HIGH = 0xF4
ERR_CTRL = 0xF5
ERR_TIMEOUT_SERVO = 0xF6
ERR_TIMEOUT_ZTEST = 0xF7
ERR_TIMEOUT_EISSETUP = 0xF8
ERR_TIMEOUT_RUN = 0xF9
ERR_TIMEOUT_SEND = 0xFA

CLEAR_USB_LATEST_ERRORS = {str(LATEST_ERRORS_DEVICE_NOT_FOUND): '', str(LATEST_ERRORS_USB_ENDPOINTS): '',
                           str(LATEST_ERRORS_USB_WRITE): ''}
"""dict of str: str: Resets all USB related latest errors.
"""
TYPES_OF_LATEST_ERRORS = len(MESSAGE_FORMATS)
"""int: The number of different errors.
"""


def new_latest_errors(errors):
    """Returns a new array to store latest errors.

    Args:
        errors: The errors that should be remembered.

    Returns:
        list of str: The list containing the latest errors in the form.

    """
    return [None if str(i) not in errors.keys() else errors[str(i)] for i in range(TYPES_OF_LATEST_ERRORS)]


def print_status(msg):
    """Logs time-coded info for debugging purposes.

    Args:
        msg (str): The message to log.

    """
    if LOG > 0:
        print "%s: %s" % (str(datetime.datetime.now()), msg)


def log_message(args, code, max_chars):
    """Logs a message to the console based on the message code.

    Args:
        args (tuple): The args to be passed to the console message format specifiers.
        code (int): The message code.
        max_chars (int): The maximum number of characters allowed per line.

    Returns:
        list of ConsoleMessage: An instance of `ConsoleMessage` per line.

    """
    if code < len(MESSAGE_FORMATS) or not code & 0xF < len(BACKEND_MESSAGES):
        msg = MESSAGE_FORMATS[code if code < len(MESSAGE_FORMATS) else ERR_USB_READ_ERROR_CODE] if code >= 0 \
            else MESSAGE_FORMATS[0]
    else:
        msg = BACKEND_MESSAGES[code & 0xF]

    if msg is None:
        return []

    if len(args):
        lines = format_file.format_string((msg % args).split(" "), max_chars * CHAR_LENGTH).split("\n")
    else:
        lines = format_file.format_string(msg.split(" "), max_chars * CHAR_LENGTH).split("\n")
    first_one = True
    console_msgs = []

    for line in lines:
        if len(line.strip(" ")) != 0:
            console_msgs.append(ConsoleMessage(line, code, not first_one))

            if first_one:
                first_one = False

    return console_msgs


class ConsoleMessage(object):
    """Console Message.

    Describes a message to be logged by the `Console` component. Since the message logged might span multiple lines,
    one `ConsoleMessage` instance is required for each line.

    Attributes:
        message (str): The message to be logged with a prefix that indicates what type of message it is e.g.
            'SUCCESS', 'ERROR'.
        code (int): The code of the message.
        color (str): The color of the box where the message will be logged.

    """
    def __init__(self, msg, c, complement=False):
        """ConsoleMessage constructor.

        Determines the color and the message prefix based on the message code.

        Args:
            msg (str): The message to be logged.
            c (int): The code of the message.
            complement (bool, optional): True if this `ConsoleMessage` is the continuation of another, False otherwise.

        """
        self.message = ("%i: " % c) if c > -1 and not complement else ""
        self.code = c

        if c == SUCCESS_MSG:
            self.color = SUCCESS_COLOR
            status = "SUCCESS: "
        elif c == REQUEST_MSG:
            self.color = REQUEST_COLOR
            status = "REQUEST: "
        elif c == ACTION_REQUIRED_MSG:
            self.color = ACTION_REQUIRED_COLOR
            status = "ACTION: "
        elif c == ACTION_CANCELED:
            self.color = ACTION_CANCELED_COLOR
            status = "CANCEL: "
        else:
            self.color = ERROR_COLOR
            status = "ERROR: "
            print_status('ERROR: 0x%02X' % c)

        if not complement:
            self.message += status

        self.message += msg

    def __str__(self):
        """Stringify an instance of `ConsoleMessage`.

        Returns:
            str: The body of the message.

        """
        return self.message
