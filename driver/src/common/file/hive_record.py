"""Hive Record class definition.

.. _src-common-file-hive_record:
    https://github.com/hivebattery/gui/blob/master/driver/src/common/file/hive_record.py

"""
import json
import os.path as path
import os
import errno
from sys import platform

from react.index import AskDirectory

from src.config.config import MAX_HISTORY_RECORDS

HOME = os.environ['HOME' if platform == 'darwin' else 'HOMEPATH']
"""str: The user's homepath.
"""
LIBRARY = path.join(HOME, 'Library/Hive Battery' if platform == 'darwin' else 'AppData\Local\Hive Battery')
"""str: The directory that will contain the .hive file.
"""
HIVE_RECORD_PATH = path.join(LIBRARY, '.hive')
"""str: The .hive file's full path.
"""


class HiveRecord:
    """Controller for .hive file.

    Enables the GUI to store user and session specific data. It is all done using a file with the name `.hive` that's
    stored in the user's library directory i.e. '$HOME/Library/Hive Battery/.hive' if running on MacOS or
    '$HOMEPATH\\AppData\\Local\\Hive Battery' if running on Windows. This .hive file starts as

        '{"default_csv_path": "SELECTED_PATH", "history": {"start_frequency": [], "end_frequency": [],
          "amplitude": []}}',

    but changes when the user updates the default csv file or runs a successful EIS session which saves the parameters
    to the corresponding entry arrays i.e. "start_frequency", "end_frequency", and "amplitude".

    Attributes:
        __indices (dict of str: int): The current index into each specific key input history.
        __prev_direc (dict of str: int): The last direction for each input history i,e. 1 if the user typed the up
            arrow key to navigate their history, -1 otherwise.
        __log ((list of (str, int)) -> None): Logs messages according to their codes. See `src.main.log_messages`.
        __record (dict): The user's custom data containing the default csv file and the entry input history arrays.
        __default_csv_path (str): The directory where all csv files will be saved.
        __history (dict of str: (list of int)): Contains the input history for each entry of the form.

    """
    def __init__(self, log):
        """Hive Record constructor.

        First, tries to open the .hive file and load the user's data. If this fails, then it prompts the user to
        select a directory to save the csv file, creates the .hive file, and finally loads the new user data to
        allow for updates.

        Args:
            log ((list of (str, int)) -> None): Logs messages according to their codes. See `src.main.log_messages`.

        Raises:
            IOError: Input/output errors when trying to read from or write to the .hive file.
            OSError: Errors related to the computer's operating system.
            Exception: If the .hive file is empty.

        """
        self.__indices = dict(start_frequency=0, end_frequency=0, amplitude=0)
        self.__prev_direc = dict(start_frequency=None, end_frequency=None, amplitude=None)
        self.__log = log
        self.__record = None
        self.__default_csv_path = None
        self.__history = None

        self.__wrote_file = False

        try:
            f = open(HIVE_RECORD_PATH, 'rb')
            self.__record = json.loads(f.read())
            f.close()

            if not len(self.__record):
                raise Exception('Empty file read.')

            self.__wrote_file = True
            self.__default_csv_path = self.__record['default_csv_path']
            self.__history = self.__record['history']

        except (IOError, OSError, Exception) as e:
            print e

            try:
                try:
                    os.mkdir(LIBRARY)
                except OSError as exc:
                    if not (exc.errno == errno.EEXIST and os.path.isdir(LIBRARY)):
                        raise

                log([('Choose a default location for .csv data...', -2)])
                default_csv_path = AskDirectory(initialdir=path.abspath(path.join(HOME, 'Documents')))

                if not len(default_csv_path):
                    raise Exception('No folder selected.')

                history = dict(start_frequency=[], end_frequency=[],
                               amplitude=[])

                self.__record = dict(default_csv_path=default_csv_path, history=history)
                self.update(("Successfully selected %s", default_csv_path))

                self.__default_csv_path = self.__record['default_csv_path']
                self.__history = self.__record['history']

            except (IOError, OSError, Exception) as e2:
                print e2
                self.__wrote_file = False
                log([("EMPTY PATH", 12)])

    @property
    def wrote_file(self):
        """bool: Whether file operations were successfully performed on the .hive file.
        """
        return self.__wrote_file

    def update(self, msgs=None):
        """Open and update .hive file.

        Assumes `self.__record` contains the user's custom data so that it can overwrite the .hive file.

        Args:
            msgs ((str, str), optional): The messages to log in case of success or failure.

        Raises:
            IOError: Input/output errors when trying to read from or write to the .hive file.
            OSError: Errors related to the computer's operating system.
            Exception: If the .hive file is empty.

        """
        msg = None
        code = None

        try:
            if self.__record is None:
                raise Exception('NULL record.')

            f = open(HIVE_RECORD_PATH, 'wb')

            f.write(json.dumps(self.__record))
            f.close()

            if msgs is not None:
                msg = msgs[0] % msgs[1]
                code = 0
                self.__wrote_file = True

        except (IOError, OSError, Exception) as e:
            print e
            self.__wrote_file = False

            if msgs is not None:
                msg = msgs[1]
                code = 12

        if msgs is not None:
            self.__log([(msg, code)])

    def change_default_path(self):
        """Update directory to save all csv files.

        Prompts the user to choose a new directory to save csv files and writes it back to the .hive file if the process
        is successful. Otherwise, logs any errors that might occur.

        Raises:
            IOError: Input/output errors when trying to read from or write to the .hive file.
            OSError: Errors related to the computer's operating system.
            Exception: If the .hive file is empty.

        """
        try:
            self.__log([('Choose a new default location for .csv data...', -2)])

            default_csv_path = AskDirectory(initialdir=self.__default_csv_path or
                                                       path.abspath(path.join(HOME, 'Documents')))

            if not len(default_csv_path):
                raise Exception('No folder selected.')

            self.__record['default_csv_path'] = default_csv_path
            self.__default_csv_path = default_csv_path
            self.update(("Successfully updated %s", default_csv_path))

        except (IOError, OSError, Exception) as e:
            if isinstance(e, Exception):
                self.__log([("'%s' remains as the default path." % self.__default_csv_path, -3)])

    def add_field_history(self, hist_dict):
        """Inserts a new value to some entry's input history.

        Writes the new history dictionary to the .hive file.

        Args:
            hist_dict (dict of str: int): Contains the new input for each entry of the form.

        """
        for (key, val) in hist_dict.items():
            history = self.__record['history'][key]
            history.append(val)

            self.__indices[key] = -1

            if len(history) > MAX_HISTORY_RECORDS:
                self.__record['history'][key] = self.__record['history'][key][1:]

        self.update()

    def poll_history(self, key, direction):
        """Navigate through the entries' input history.

        Goes through the history saved to the .hive file starting with the newest input (if the direction is 1) or
        with the oldest (if the direction is -1).

        Args:
            key (str): The name of the entry whose history's being navigated.
            direction (int): 1 if navigating from the newest entry to the oldest, -1 otherwise.

        Returns:
            str: The input at the position determined by `self.__indices` and the direction.

        """
        if len(self.__record['history'][key]) == 0:
            return ''

        prev_direc = self.__prev_direc[key]

        self.__indices[key] -= 1 * direction

        if prev_direc is not None and prev_direc != direction:
            self.__indices[key] -= 1 * direction
            self.__prev_direc[key] = direction

        if direction == 1 and self.__indices[key] + 1 == -len(self.__record['history'][key]):
            self.__indices[key] = -1
        elif direction == -1 and self.__indices[key] == len(self.__record['history'][key]):
            self.__indices[key] = 0

        return self.__record['history'][key][self.__indices[key]]
