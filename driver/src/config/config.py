"""GUI Configuration.

Provides a quick and easy way to configure certain aspects of the GUI via global variables.

"""

#: Configuration params
LOG = 0
"""int: Determines what kind of logging should occur. 0 means no logging, 1 means light logging e.g. status updates
about actions and the EIS parameters, and 2 means logging everything.
"""
DEV = False
"""bool: True if the GUI should simulate a device connection, False otherwise.
"""
F_MIN = 3.72529
"""float: The minimum frequency.
"""
N_SAMPLES = 128
"""int: The number of samples.
"""
N_PERIODS = 8
"""int: The number of periods.
"""
MAX_HISTORY_RECORDS = 10
"""int: The max number of input stored in the entries' input history arrays.
"""

#: Aesthetics
BG_COLOR = '#%02x%02x%02x' % (56, 59, 61)
"""str: Background color.
"""
FG_COLOR = '#%02x%02x%02x' % (43, 43, 43)
"""str: Foreground color.
"""
TEXT_COLOR = '#%02x%02x%02x' % (195, 198, 184)
"""str: The color for all written text.
"""
BUTTON_BG = '#%02x%02x%02x' % (81, 86, 88)
"""str: The color to paint the background of buttons.
"""
SUCCESS_COLOR = '#B9F6CA'
"""str: The color associated with successful results.
"""
REQUEST_COLOR = '#FFF9C4'
"""str: The color associated with ongoing requests.
"""
ACTION_REQUIRED_COLOR = '#81D4FA'
"""str: The color indicating the user needs to perform some action to continue.
"""
ACTION_CANCELED_COLOR = '#FFAB91'
"""str: The color indicating an action was cancelled by a user.
"""
ERROR_COLOR = '#EF9A9A'
"""str: The color associated with failures.
"""
WIDTH = 1000
"""int: The width of the GUI. The height is the golden ratio of the width.
"""
