"""GUI class definition.

.. _src-gui:
    https://github.com/hivebattery/gui/blob/master/driver/src/components/gui.py

"""
from __future__ import absolute_import
from decimal import Decimal

import react.index as react_ctrl
from react.component import Component

from src.actions.actions import *
from src.common.bytes import bytes
from src.common.data_structures.queue import Queue
from src.common.file import csv_files
from src.common.file.hive_record import HiveRecord
from src.common.log.console_message import print_status
from src.components.console import Console
from src.components.main_dashboard import MainDashboard
from src.components.toggles_dashboard import TogglesDashboard
from src.config.config import LOG
from src.reducers.index import root_reducer
from src.config.config import F_MIN, WIDTH, N_PERIODS, N_SAMPLES


def map_state_to_props(state):
    return dict(data=state.usb.data, is_device_connected=state.usb.is_connected, usb_handle=state.usb.usb_handle,
                usb_error=state.usb.error, usb_message=state.usb.message, usb_status=state.usb.status,
                current_range=state.usb.current_range)


class GUI(Component):
    """GUI Component.

        The React Component that defines the entire GUI and initializes all components and some of
        their event handlers.

        Attributes:
            n_freqs_str_var (react.widget_wrappers.StringVar): Holds the value indicating the number of frequencies
                selected by the user.
            amplitude_str_var (react.widget_wrappers.StringVar): Holds the value indicating the amplitude selected by
                the user.
            amplitude_int_var (react.widget_wrappers.IntVar): Holds the value indicating the type of amplitude i.e.
                either current or voltage.
            main_dashboard (src.components.main_dashboard.MainDashboard): Contains either the Nyquist plot or the
                waiting screen.
            console (src.components.console.Console): Contains the console that logs the program's progress.
            toggles_db (src.components.toggles_dashboard.TogglesDashboard): Contains the form and the buttons.
            filemenu (react.widget_wrappers.Menu): The 'File' menu with the option to change the default path to save
                csv files.
            status_queue (src.common.data_structures.queue.Queue of (int, tuple)): The FIFO where ongoing EIS data
                transfers sends any status updates or errors together with their code.

    """
    def __init__(self):
        """GUI Constructor.

        The initialization process happen according to the following steps:
            1) Configure React's logging feature and initialize Tkinter's root.
            2) Connect the USB actions with the reducer and this component.
            3) Create the GUI's mainframe.
            4) Set up the state and the components.
            5) Set up 'File' menu.
            6) Initialize status queue and props.
            7) Initialize timers, the .hive record, and start the Tkinter mainloop.

        """
        react_ctrl.config(log=LOG)  #: Step 1

        react_ctrl.new_root(WIDTH, WIDTH / react_ctrl.GOLDEN_RATIO, center=True, resizable=(False, False),
                            title='Hive Battery', bg="black")

        #: Step 2
        actions = dict(usb=dict(connect=connect, start_eis=start_eis, check_connection=check_connection,
                                poll_eis=poll_eis, start_eis_data_transfer=start_eis_data_transfer,
                                update_usb_status=update_usb_status))

        super(GUI, self).__init__(None, frame=react_ctrl.get_mainframe(), actions=actions,
                                  map_state_to_props=map_state_to_props, root_reducer=root_reducer)

        react_ctrl.set_app(self)  #: Step 3

        #: Step 4
        self.state = dict(form_validated=False, data=[], console_msgs=[], new_msgs=[],
                          latest_errors=new_latest_errors({}), start_frequency=None, end_frequency=None, n_freqs=0,
                          amplitude=0, hive_record_ready=False, attempted_write=False, error_default_path=False,
                          columnspan=4)

        # StringVars
        self.n_freqs_str_var = react_ctrl.StringVar()
        self.amplitude_str_var = react_ctrl.StringVar()

        # IntVars
        self.amplitude_int_var = react_ctrl.IntVar()

        curr_width = WIDTH / react_ctrl.GOLDEN_RATIO

        self.main_dashboard = MainDashboard(self, frame=react_ctrl.get_mainframe(), width=curr_width, height=curr_width,
                                            x=curr_width / react_ctrl.GOLDEN_RATIO, y=0,
                                            is_device_connected=self.props.is_device_connected, data=self.props.data,
                                            hive_record_ready=self.state.hive_record_ready,
                                            freqs_explicit=lambda: self.freqs_explicit)

        curr_width /= react_ctrl.GOLDEN_RATIO

        self.console = Console(self, frame=react_ctrl.get_mainframe(), width=curr_width, height=curr_width, x=0, y=0,
                               console_msgs=self.state.console_msgs, new_msgs=self.state.new_msgs,
                               update_console_messages=self.update_console_messages,
                               clear_new_msgs=self.clear_new_msgs, columnspan=self.state.columnspan)

        curr_width /= react_ctrl.GOLDEN_RATIO

        self.toggles_db = TogglesDashboard(self, frame=react_ctrl.get_mainframe(),
                                           width=curr_width * react_ctrl.GOLDEN_RATIO, height=curr_width, x=0,
                                           y=curr_width * react_ctrl.GOLDEN_RATIO,
                                           # OTHER PROPS
                                           is_device_connected=self.props.is_device_connected,
                                           # SHARED PROPS
                                           form_validated=self.state.form_validated,
                                           # FORM PROPS
                                           toggle_form=self.toggle_form,
                                           latest_errors=self.state.latest_errors,
                                           on_form_validated=self.on_form_validated, update_freqs=self.update_freqs,
                                           log_messages=self.log_messages, n_freqs_str_var=self.n_freqs_str_var,
                                           n_freqs=self.state.n_freqs, amplitude_str_var=self.amplitude_str_var,
                                           amplitude_int_var=self.amplitude_int_var,
                                           clear_latest_errors=self.clear_latest_errors,
                                           update_latest_errors=self.update_latest_errors,
                                           poll_history=lambda key, d: self.hive_record.poll_history(key, d),
                                           # BUTTON PROPS
                                           on_start_eis=self.on_start_eis, on_stop_eis=self.on_start_eis,
                                           usb_error=self.props.usb_error, usb_status=self.props.usb_status,
                                           change_default_path=self.change_default_path,
                                           hive_record_ready=self.state.hive_record_ready,
                                           attempted_write=self.state.attempted_write,
                                           init_hive_record=self.init_hive_record,
                                           error_default_path=self.state.error_default_path,
                                           columnspan=self.state.columnspan)

        #: Step 5
        self.filemenu = react_ctrl.Menu(react_ctrl.get_top_menu(), tearoff=0)
        self.filemenu.add_command(label="Change default csv path...", command=lambda: self.change_default_path()
                                  if self.state.hive_record_ready else self.init_hive_record())

        react_ctrl.add_submenu(self.filemenu, 'File')

        self.status_queue = Queue(self.new_status_code)  #: Step 6

        self.__progress_timer = None
        self.__connection_timer = None
        self.__freqs_explicit = None
        self.__current_range = None
        self.__battery_voltage = None
        self.__hive_record = None
        self.__start_time = None
        self.__block_actions = False
        self.__fetching_data = False

        #: Step 7
        self.init_gui()

    @property
    def connection_timer(self):
        """Tkinter.after: Timer that checks the USB connection with the device.

        Every few milliseconds, this timer triggers an event that calls on an action to either connect to the device
        or check the connection once it's connected.
        """
        return self.__connection_timer

    @connection_timer.setter
    def connection_timer(self, value):
        self.__connection_timer = value

    @property
    def progress_timer(self):
        """Tkinter.after: Timer that reads the USB status code.

        Every few milliseconds, this timer triggers an event that calls on an action to check the current status of the
        device.
        """
        return self.__progress_timer

    @progress_timer.setter
    def progress_timer(self, value):
        self.__progress_timer = value

    @property
    def freqs_explicit(self):
        """list of str: The explicit number of mHz for each frequency.
        """
        return self.__freqs_explicit

    @freqs_explicit.setter
    def freqs_explicit(self, value):
        self.__freqs_explicit = value

    @property
    def current_range(self):
        """float: The current ranging returned by the device.
        """
        return self.__current_range

    @current_range.setter
    def current_range(self, value):
        self.__current_range = value

    @property
    def battery_voltage(self):
        """float: The battery voltage value returned by the device.
        """
        return self.__battery_voltage

    @battery_voltage.setter
    def battery_voltage(self, value):
        self.__battery_voltage = value

    @property
    def hive_record(self):
        """src.common.file.hive_record.HiveRecord: The HiveRecord instance to interact with the .hive file.
        """
        return self.__hive_record

    @hive_record.setter
    def hive_record(self, value):
        self.__hive_record = value

    @property
    def start_time(self):
        """datetime: The starting time for an EIS session.
        """
        return self.__start_time

    @start_time.setter
    def start_time(self, value):
        self.__start_time = value

    @property
    def block_actions(self):
        """bool: True if timers should not trigger actions, False otherwise.
        """
        return self.__block_actions

    @block_actions.setter
    def block_actions(self, value):
        self.__block_actions = value

    @property
    def fetching_data(self):
        """bool: True if the device is currently sending data to the computer, False otherwise.
        """
        return self.__fetching_data

    @fetching_data.setter
    def fetching_data(self, value):
        self.__fetching_data = value

    def init_gui(self):
        """Initialize GUI.

        Starts timers, renders all components, initializes .hive record, and starts Tkinter's mainloop.

        """
        self.init_timers()

        self.render()

        react_ctrl.set_immediate(self.init_hive_record)
        react_ctrl.get_root().mainloop()

    def init_timers(self):
        """Initialize timers.

        Starts the connection and progress timers with their respective callbacks, setting `self.connection_timer` to
        call back `self.connect` since this is the first connection attempt to the device.

        """
        self.connection_timer = react_ctrl.set_immediate(self.connect)
        self.progress_timer = react_ctrl.set_immediate(self.poll_eis_status)

    def init_hive_record(self):
        """Attempts to initialize the .hive record.

        In order to prevent crashes, this method momentarily suspends all actions while trying to load the user's custom
        data. Once it has succeeded or failed, the actions are resumed and the state is updated to reflect the results
        of the .hive record initialization attempt.

        """
        if LOG > 0:
            print_status("INIT HIVE RECORD")

        self.block_actions = True
        self.hive_record = HiveRecord(self.log_messages)
        self.block_actions = False

        self.set_state(dict(hive_record_ready=self.hive_record.wrote_file, attempted_write=True))

    def change_default_path(self):
        """Change default path to save csv files.

        When triggered, this callback opens up a dialog to prompt the user to choose a new path and save it back into
        the .hive file. Actions are also momentarily suspended and then renewed to prevent crashes.

        """
        self.block_actions = True
        self.hive_record.change_default_path()
        self.block_actions = False

        if self.state.error_default_path is self.hive_record.wrote_file:
            self.set_state(dict(error_default_path=not self.hive_record.wrote_file))

    def component_will_receive_props(self, props):
        """Overrides Component's `component_will_receive_props`.

        Inspects new props to determine what changes should be made to reflect the GUI's new state.

        Args:
            props: The new props that haven't been updated on this component.

        """
        msgs = []
        latest_errors = None
        callbacks = []

        #: Props related to the connection and disconnection of the device.
        if hasattr(props, 'is_device_connected'):
            if self.props.is_device_connected != props.is_device_connected:
                if props.is_device_connected:
                    msgs.append(("Connected to device.", 0))
                    latest_errors = CLEAR_USB_LATEST_ERRORS
                else:
                    callbacks.append((0, lambda: self.set_state(dict(form_validated=False))))

        #: Props related to the state read at the device.
        if hasattr(props, 'usb_status'):
            if self.props.usb_status != props.usb_status:
                msg = None

                if props.usb_status != sTRANS:
                    self.fetching_data = False

                if props.usb_status == sBUSY:
                    msg = "Waiting for EIS to finish..."
                elif props.usb_status == sSIGN:
                    pass
                elif props.usb_status == sDAV:
                    freq_id = 0 if self.props.data is None else len(self.props.data)
                    msg = "Data available. Requesting frequency number %i..." % (freq_id + 1)

                    self.block_actions = True

                    if self.state.n_freqs - freq_id > 0:
                        callbacks.append((0, lambda: self.props.usb.start_eis_data_transfer(self.props.usb_handle,
                                                                                            self.status_queue,
                                                                                            freq_id)))

                if msg is not None:
                    msgs.append((msg, (-1 if props.usb_status != sSIGN else 0)))

        #: Props related to messages generated by usb actions.
        if hasattr(props, 'usb_message'):
            if self.props.usb_message != props.usb_message:
                if props.usb_message is not None:
                    for usb_message in props.usb_message:
                        msgs.append(usb_message)

        #: Props related to the voltage and current data returned by the device.
        if hasattr(props, 'data'):
            if props.data is not None and (self.props.data is None or len(self.props.data) != len(props.data)):
                self.block_actions = False
                freqs_left = self.state.n_freqs - len(props.data)
                freq_id = 0 if self.props.data is None else len(self.props.data)

                msgs.append(("Received data. %i frequenc%s left." % (freqs_left, "ies" if freqs_left != 1 else 'y'),
                             0))

                if freqs_left <= 0:
                    msgs.append(("Done with %i frequencies." % self.state.n_freqs, 0))

                    callbacks.append((0,
                                      lambda: csv_files.write_current_voltage_csv(self.hive_record.default_csv_path,
                                                                                  'test_raw', self.props.data,
                                                                                  self.freqs_explicit,
                                                                                  N_SAMPLES, N_PERIODS,
                                                                                  self.current_range,
                                                                                  self.battery_voltage,
                                                                                  '0123456789', self.start_time,
                                                                                  self.log_messages)))

                    if self.toggles_db.buttons.force_disabled:
                        self.toggles_db.buttons.toggle_force_disable()

        #: Props related to usb errors.
        if hasattr(props, 'usb_error'):
            if self.props.usb_error != props.usb_error:
                if props.usb_error[0] is not None:
                    error, args = props.usb_error
                    msgs.append((args if args is not None else (), error))

                    self.block_actions = False

                    if self.toggles_db.buttons.force_disabled:
                        self.toggles_db.buttons.toggle_force_disable()

        #: Update props on this components.
        self.ready_props(props)

        #: Log any messages generated.
        if len(msgs) > 0:
            self.log_messages(msgs, latest_errors)

        #: Call any pending callbacks
        if len(callbacks) > 0:
            for mseconds, callback in callbacks:
                react_ctrl.set_timeout(mseconds, callback)

    def new_status_code(self):
        """`self.status_queue` callback.

        Handles a new status code during an ongoing EIS data transfer. The status code is first identified and matched
        to a scenario, thus handling whatever situation happening at the device.

        """
        for (status, args) in self.status_queue:
            if status == sTRANS:
                if not self.fetching_data:
                    self.fetching_data = True
                    self.log_messages([("Receiving data...", -1)])
            elif status == sDAV:
                pass
            else:
                self.current_range = args[0]
                self.battery_voltage = bytes.bytes_to_double(args[1:])[0]

            self.props.usb.update_usb_status(status)

    def connect(self):
        """Attempt to connect to the device.

        Determine the action required by the current situation, that is, if the device is connected, then there should
        be a connection check, otherwise, a new attempt to connect to the device is needed.

        This callback generates an infinite loop by calling itself that enables the callback to be called every half
        a second.

        """
        if not self.block_actions:
            if not self.props.is_device_connected:
                self.props.usb.connect()
            else:
                self.props.usb.check_connection()

        react_ctrl.set_timeout(500, self.connect)

    def poll_eis_status(self):
        """Read the status code at the device.

        If the device is connected, then this method reads the status code every 150 milliseconds to quickly detect
        any change in the device. On the other hand, if the device is not connected, keep on calling this timer
        anyway but every half a second instead.

        """
        if not self.block_actions and self.props.is_device_connected:
            timeout = 150
            self.props.usb.poll_eis(self.props.usb_handle)
        else:
            timeout = 500

        react_ctrl.set_timeout(timeout, self.poll_eis_status)

    def log_messages(self, messages, latest_errors=None):
        """Log new messages.

        Update the state of this component to reflect new messages that need to be logged and pass this information
        down to the Console component as props.

        Args:
            messages (list of (str, int)): The messages to be logged plus their respective codes.
            latest_errors (dict of str: str, optional): Any errors that should be remembered to prevent logging the
                same message twice.

        """
        state = dict(new_msgs=(self.state.new_msgs + messages))

        if latest_errors is not None:
            state['latest_errors'] = self.state.latest_errors[:]

            for item in latest_errors.items():
                key, val = item
                state['latest_errors'][int(key)] = val

        self.set_state(state)

    def clear_new_msgs(self):
        """Indicate that all messages have been logged and can now be deleted.

        """
        self.set_state(dict(new_msgs=[]))

    def clear_latest_errors(self):
        """Erase all tracks of previous errors.

        """
        self.set_state(dict(latest_errors=new_latest_errors({})))

    def update_latest_errors(self, errors):
        """Add new errors to be remembered.

        Args:
            errors (dict of str: str): The errors to be remembered.

        """
        out = {}

        for i in range(len(self.state.latest_errors)):
            if str(i) not in errors.keys():
                out[str(i)] = self.state.latest_errors[i]

        self.set_state(dict(latest_errors=new_latest_errors(out)))

    def update_console_messages(self, console_msgs):
        """Update the list that contains all logged messages with the messages most recently passed down to the console.

        Args:
            console_msgs (list of (int, str)): The updated list of messages.

        """
        self.set_state(dict(console_msgs=console_msgs))

    def update_freqs(self, start_frequency, end_frequency, n_freqs):
        """Pass up the validated form input to this component pertaining to frequencies.

        Args:
            start_frequency (float): The lower bound for the frequencies.
            end_frequency (float): The upper bound for the frequencies.
            n_freqs (int): The number of frequencies requested.

        """
        self.set_state(dict(start_frequency=start_frequency, end_frequency=end_frequency, n_freqs=n_freqs))

    def on_form_validated(self, start_frequency, end_frequency, n_freqs, amplitude):
        """Pass up the validated form input to this component pertaining to frequencies and amplitude.

        Args:
            start_frequency (int): The lower bound for the frequencies.
            end_frequency (int): The upper bound for the frequencies.
            n_freqs (int): The number of frequencies requested.
            amplitude (int): The amplitude.

        """
        self.set_state(dict(start_frequency=start_frequency, end_frequency=end_frequency, n_freqs=n_freqs,
                            amplitude=amplitude))

    def toggle_form(self, val):
        """Validate or invalidate form.

        Args:
            val (bool): True if all the input is correct, False otherwise.

        """
        self.set_state(dict(form_validated=val))

    def on_start_eis(self):
        """Send start EIS request to the device.

        Given the validated form, do the following steps:
            1) Disable the form and save the correct input to each entry's input history in the .hive record.
            2) Extract all parameters from the form and check whether the request includes just a single frequency or
                more.
            3) Calculate the explicit binary string representing the frequencies requested and print all the request
                parameters to the console.
            4) Start EIS with the specified parameters, making a note of the starting time.

        """
        self.toggles_db.buttons.toggle_force_disable()  #: Step 1

        history_dict = dict(start_frequency=int(self.toggles_db.form.start_frequency_en.get(), 10),
                            amplitude=self.state.amplitude)

        amplitude_type = self.amplitude_int_var.get()  #: Step 2
        amplitude = self.state.amplitude

        freqs_exp = [self.state.start_frequency, self.state.end_frequency]
        n_freqs = self.state.n_freqs

        if freqs_exp[1] is None:  #: Step 3
            freq_bytes = bin(2 ** freqs_exp[0])[2:].zfill(24)
            self.freqs_explicit = bytes.map_ones_to_decimal(freq_bytes, factor=F_MIN)[:1]
            msg = "Requesting EIS with %i frequency (mHz): %.2E," % (n_freqs, (Decimal(self.freqs_explicit[0]) / 1000))
        else:
            history_dict['end_frequency'] = int(self.toggles_db.form.end_frequency_en.get(), 10)
            freq_bytes = "".join("0" for i in range(23 - freqs_exp[1]))
            freq_bytes += bin(int(bytes.balance_binary_string(F_MIN,
                                                              2 ** (freqs_exp[1] - freqs_exp[0] - 1)
                                                              * F_MIN, n_freqs - 2),
                                  2))[2:]
            freq_bytes += "".join("0" for i in range(freqs_exp[0]))

            self.freqs_explicit = bytes.map_ones_to_decimal(freq_bytes, factor=F_MIN)

            msg = "Requesting EIS with %i frequencies (Hz): %s" % \
                  (n_freqs, ", ".join(['%.2E' % (Decimal(freq_exp) / 1000) for freq_exp in self.freqs_explicit[:-1]]))

            if len(self.freqs_explicit[:-1]) > 1:
                msg += ","

            msg += " and %.2E" % (Decimal(self.freqs_explicit[-1]) / 1000) + ","

        msg += " and amplitude (mV): %i." % amplitude

        self.log_messages([(msg, -1)])
        self.hive_record.add_field_history(history_dict)

        self.start_time = datetime.datetime.now()  #: Step 4
        self.props.usb.start_eis(self.props.usb_handle, freq_bytes, amplitude, amplitude_type, N_SAMPLES, N_PERIODS)

    def render(self):
        """GUI Render method.

        Indicate that the widgets are ready to be displayed and render all components.

        """
        react_ctrl.widgets_ready()

        self.main_dashboard.render()
        self.console.render()
        self.toggles_db.render()
