"""Form Component class definition.

Todo:
    * Clean up input verification via Tkinter's `validatecommand` and `invalidcommand` `Entry` methods, which would
        also allow for less event bindings.

.. _src-components-form:
    https://github.com/hivebattery/gui/blob/master/driver/src/components/form.py

"""
from __future__ import absolute_import

import re

from react.index import StringVar, IntVar, Label, Frame, Entry, Scale, Radiobutton, Checkbutton, HORIZONTAL,\
                        END, GOLDEN_RATIO, set_immediate
from react.component import Component

from src.common.log.console_message import *
from src.common.bytes import bytes
from src.config.config import *

MAX_VALS_FREQS = [F_MIN, F_MIN * 2 ** 23]
"""list of float: The lower and upper bounds for valid frequency values.
"""


class Form(Component):
    """Form Component.

    The React Component that contains the GUI's form i.e. the entries, the radio buttons, the checkbox, and the
    scale through which the user inputs the EIS parameters.

    Attributes:
        __n_middle_bits (int): The number of bits between the lowest and the highest frequencies.
        __start_frequency_str_var (react.widget_wrappers.StringVar): Holds the input of the 'start frequency' entry.
        __end_frequency_str_var (react.widget_wrappers.StringVar): Holds the input of the 'end frequency' entry.
        __single_frequency_str_var (react.widget_wrappers.IntVar): Holds the 'single frequency' checkbox value.
        fields_frame (react.widget_wrappers.Frame): Contains the left side of the form with all the entries.
        other_frame (react.widget_wrappers.Frame): Contains the right side of the form.
        single_freq_lb (react.widget_wrappers.Label): 'Single frequency' label.
        start_frequency_lb (react.widget_wrappers.Label): 'Start frequency' label.
        end_frequency_lb (react.widget_wrappers.Label): 'End frequency' label.
        n_freqs_lb (react.widget_wrappers.Label): 'Number of frequencies' label.
        n_freqs_int (react.widget_wrappers.Label): The actual number of frequencies.
        amplitude_lb (react.widget_wrappers.Label): 'Amplitude' label.
        start_frequency_en (react.widget_wrappers.Entry): Start frequncy entry.
        end_frequency_en (react.widget_wrappers.Entry): End frequency entry.
        amplitude_en (react.widget_wrappers.Entry): End frequency entry.
        n_freqs_scale (react.widget_wrappers.Scale): Allows the user to input how many frequencies should be requested.
        amplitude_rb_v (react.widget_wrappers.Radiobutton): Allows the user to select 'Voltage'.
        amplitude_rb_c (react.widget_wrappers.Radiobutton): Allows the user to select 'Current'.
        single_freq_cb_v (react.widget_wrappers.Checkbutton): Allows the user to request a single frequency.
        entries (list of react.widget_wrappers.Entry): Provides an easy way to refer to all entries in the form at once.

    """
    def __init__(self, parent, frame=None, **props):
        """Form Component constructor.

        Args:
            parent (react.component.Component): The component that should contain the form.
            frame (react.widget_wrappers.Frame, optional): The Frame where the form should be placed. If no
                frame is specified, then the default frame is considered instead.
            **props: The props passed down to the Form component.

        """
        super(Form, self).__init__(parent, frame, **props)

        self.state = dict(single_frequency=False)

        self.__n_middle_bits = -1

        # StringVars
        self.__start_frequency_str_var = StringVar()
        self.__end_frequency_str_var = StringVar()

        # IntVars
        self.__single_frequency_int_var = IntVar()

        # Frame
        self.fields_frame = Frame(self, width=self.height, height=self.height, frame=self.parent_frame, bg=BG_COLOR)
        self.other_frame = Frame(self, width=self.height * GOLDEN_RATIO, height=self.height, frame=self.parent_frame,
                                 bg=BG_COLOR)

        # Labels
        self.single_freq_lb = Label(self, "Single frequency", frame=self.fields_frame, bg=BG_COLOR, fg=TEXT_COLOR,
                                    font=("Helvetica", 12))
        self.start_frequency_lb = Label(self, "Start frequency (mHz):", frame=self.fields_frame, bg=BG_COLOR,
                                        fg=TEXT_COLOR, font=("Helvetica", 12))
        self.end_frequency_lb = Label(self, "End frequency (mHz):", frame=self.fields_frame, bg=BG_COLOR,
                                      fg=TEXT_COLOR, font=("Helvetica", 12))
        self.n_freqs_lb = Label(self, "No. of frequencies:", frame=self.other_frame, bg=BG_COLOR, fg=TEXT_COLOR,
                                font=("Helvetica", 12), width=20)
        self.n_freqs_int = Label(self, self.props.n_freqs_str_var, frame=self.other_frame, bg=BG_COLOR, fg=TEXT_COLOR,
                                 font=("Helvetica", 12))
        self.amplitude_lb = Label(self, "Amplitude (mV):", frame=self.fields_frame, bg=BG_COLOR, fg=TEXT_COLOR,
                                  font=("Helvetica", 12))

        # Entries
        self.start_frequency_en = Entry(self, self.__start_frequency_str_var, frame=self.fields_frame)
        self.end_frequency_en = Entry(self, self.__end_frequency_str_var, frame=self.fields_frame)
        self.amplitude_en = Entry(self, self.props.amplitude_str_var, frame=self.fields_frame)

        # Scale
        self.n_freqs_scale = Scale(self, frame=self.other_frame, bg=BG_COLOR, from_=2, orient=HORIZONTAL,
                                   command=self.update_n_freqs_sc, troughcolor=FG_COLOR, sliderrelief='flat',
                                   highlightbackground=BG_COLOR, activebackground=BG_COLOR, bd=1,
                                   highlightcolor=BG_COLOR, highlightthickness=0)

        # Radiobuttons
        self.amplitude_rb_v = Radiobutton(self, "Voltage", self.props.amplitude_int_var, 0, frame=self.other_frame,
                                          command=lambda: self.on_amplitude_type_change(), bg=BG_COLOR, fg=TEXT_COLOR,
                                          font=("Helvetica", 12))
        self.amplitude_rb_c = Radiobutton(self, "Current", self.props.amplitude_int_var, 1, frame=self.other_frame,
                                          command=lambda: self.on_amplitude_type_change(), bg=BG_COLOR, fg=TEXT_COLOR,
                                          font=("Helvetica", 12))

        # Checkbuttons
        self.single_freq_cb_v = Checkbutton(self, None, self.__single_frequency_int_var, 0,
                                            frame=self.fields_frame,
                                            command=lambda: self.toggled_single_frequency(), bg=BG_COLOR, fg=BG_COLOR,
                                            activebackground=BG_COLOR, highlightcolor=BG_COLOR,
                                            highlightbackground=BG_COLOR, selectcolor=BG_COLOR,
                                            activeforeground=BG_COLOR, disabledforeground=BG_COLOR, bd=0,
                                            offrelief='flat')

        self.entries = [self.start_frequency_en, self.end_frequency_en, self.amplitude_en]

        for entry in self.entries:  #: Configure entries and set up the events they should handle.
            entry.config(background=FG_COLOR, borderwidth=0, relief='flat', foreground=TEXT_COLOR,
                         width=8, highlightthickness=1, insertbackground="white", disabledbackground=BG_COLOR,
                         selectbackground=TEXT_COLOR, selectforeground="black")
            entry.bind("<ButtonRelease-1>", self.clear_entry)
            entry.bind("<FocusIn>", self.clear_entry)
            entry.bind("<FocusOut>", self.update_n_freqs_sc)

        #: Set up all other event handling
        self.start_frequency_en.bind("<Up>", lambda e: self.pressed_key(e, 'start_frequency', 1))
        self.end_frequency_en.bind("<Up>", lambda e: self.pressed_key(e, 'end_frequency', 1))
        self.amplitude_en.bind("<Up>", lambda e: self.pressed_key(e, 'amplitude', 1))

        self.start_frequency_en.bind("<Down>", lambda e: self.pressed_key(e, 'start_frequency', -1))
        self.end_frequency_en.bind("<Down>", lambda e: self.pressed_key(e, 'end_frequency', -1))
        self.amplitude_en.bind("<Down>", lambda e: self.pressed_key(e, 'amplitude', -1))

    def component_will_receive_props(self, props):
        """Overrides Component's `component_will_receive_props`.

        Validate the form's input if the device is reconnected or blur all entries if the device has just been
        disconnected.

        Args:
            props: The new props that haven't been updated on this component.

        See Also:
            React module :py:mod:`component`.

        """
        if hasattr(props, 'is_device_connected'):
            if self.props.is_device_connected != props.is_device_connected:
                if props.is_device_connected:
                    set_immediate(self.update_n_freqs_sc)
                else:
                    set_immediate(self.parent_frame.focus)

    def on_bg_click(self):
        """Background click event handler to blur all entries.

        See Also:
            React's main module :py:mod:`react-index`

        """
        for entry in self.entries:
            entry.selection_clear()

    def pressed_key(self, e, key, direction):
        """Up and down keys handler.

        Provides the required functionality for the user to be able to navigate through each entry's input history
        using the .hive file.

        Args:
            e (Tkinter.Event): The event object generate by Tkinter when the user presses the up or down arrow keys.
            key (str): The key to match the correct entry's input history in the .hive file.
            direction (int): 1 if the user pressed the up arrow key, -1 otherwise.

        """
        new_str = str(self.props.poll_history(key, direction))

        if len(new_str) > 0:
            e.widget.delete(0, END)
            e.widget.insert(0, new_str)

    @staticmethod
    def clear_entry(e):
        """Clear all text in the entry.

        Args:
            e (Tkinter.Event): The Tkinter event object generated by the entry.

        """
        entry = e.widget
        entry.select_range(0, END)

    def toggled_single_frequency(self):
        """Enable a single frequency request.

        Sets the state of the component to the current choice of single or multiple frequencies and validates the input.

        """
        self.set_state(dict(single_frequency=bool(self.__single_frequency_int_var.get())))
        self.update_n_freqs_sc()

    def update_n_freqs_sc(self, e=None):
        """Validates form input.

        Checks all entries and user input by applying the necessary constraints to each widget. These operations happen
        in the following order:

            1) Check if the entries are empty.
            2) If the amplitude entry is not empty or all frequency entries are not empt, procced with validation:
                a) If the frequency entries are not empty, validate them and decide whether the right side of the
                    form should be displayed.
                b) If the amplitude entry is not empty, validate it.
            3) If validation was successful, configure the scale so that users may select the number of frequencies to
                request.
            4) Toggle the form reflecting the state of the validation so that this component's parent knows about the
                input.

        Args:
            e (Tkinter.Event, optional): The Tkinter event object generated by the entry. None implies the validation
                was triggered programmatically rather than by Tkinter's event loop.

        """
        is_start_freq_empty = self.start_frequency_en.is_empty()  #: Step 1
        is_end_freq_empty = self.end_frequency_en.is_empty()
        is_amplitude_empty = self.amplitude_en.is_empty()

        if e is not None and bool(re.search('entry', e if isinstance(e, str) else str(e.widget))):
            e.widget.selection_clear()

        hide_freqs = True
        form_validated = False

        #: Step 2
        if not ((is_start_freq_empty or (is_end_freq_empty and self.state.single_frequency)) and is_amplitude_empty):
            if not is_start_freq_empty and (self.state.single_frequency or not is_end_freq_empty):  #: Step 2.a
                [start_freq_code, end_freq_code, freq_range_code] = self.check_freqs()
                clean_messages = {}

                if start_freq_code == 0:
                    clean_messages[str(LATEST_ERRORS_START_FREQ)] = True

                if end_freq_code == 0:
                    clean_messages[str(LATEST_ERRORS_END_FREQ)] = True

                if freq_range_code == 0:
                    clean_messages[str(LATEST_ERRORS_RANGE)] = True

                hide_freqs = len(clean_messages) != 3

                if len(clean_messages) > 0:
                    self.props.update_latest_errors(clean_messages)

            if not is_amplitude_empty:  #: Step 2.b
                form_validated = self.check_amplitude() and not hide_freqs

        if not hide_freqs:  #: Step 3
            self.configure_scale(form_validated)

        self.props.toggle_form(form_validated)  #: Step 4

    def on_amplitude_type_change(self):
        """Validate form after selecting 'Voltage' or 'Current' with the radio buttons.

        If the amplitude entry is not empty, programmatically fire `self.update_n_freqs_sc`.

        """
        if not self.amplitude_en.is_empty():
            self.update_n_freqs_sc(None)

    def check_amplitude(self):
        """Validate amplitude entry.

        Two important checks happen during this method:

            1) Whether the user typed an integer.
            2) Whether the integer input lies within the acceptable bounds.

        In case of error, change the color of text to indicate invalid input and save these errors to the latest errors
        list tracker so that the user only gets notified about each error once. If validation was successful, change
        back the text of the entry to reflect valid input.

        Raises:
            ValueError: If the user input is not an integer.

        """
        amplitude_str = re.sub(" ", "", self.amplitude_en.get())
        args = None

        try:  #: Check 1
            amplitude_int = int(amplitude_str, 10)
            upper_bound = 30 - 10 * self.props.amplitude_int_var.get()

            if not 0 <= amplitude_int <= upper_bound:  #: Check 2
                args = "Amplitude", amplitude_int, 0, upper_bound
                code = 1

            else:
                code = 0

        except ValueError:
            args = amplitude_str, 'integer'
            code = 2

        if code != 0:
            color = ERROR_COLOR

            if self.props.latest_errors[3] != amplitude_str:
                self.props.log_messages([(args, code)], {str(LATEST_ERRORS_AMPLITUDE): amplitude_str})
        else:
            color = TEXT_COLOR
            self.props.update_latest_errors({str(LATEST_ERRORS_AMPLITUDE): True})

        self.amplitude_en.configure(foreground=color)

        return color == TEXT_COLOR

    def check_freqs(self):
        """Validate frequency entries.

        Three important checks happen during this method:

            1) Whether the user typed an integer.
            2) Whether the integer input lies within the acceptable bounds.
            3) If applicable, whether the lower bound is compatible with the upper bound.

        In case of error, change the color of text to indicate invalid input and save these errors to the latest errors
        list tracker so that the user only gets notified about each error once. If validation was successful, change
        back the text of the entry to reflect valid input.

        Raises:
            ValueError: If the user input is not an integer.

        """
        freq_en = [self.start_frequency_en]
        freqs_int = []
        codes = [None, None, 0]

        if not self.state.single_frequency:
            freq_en.append(self.end_frequency_en)
        else:
            codes[1] = 0

        args = [None for i in range(3)]
        freqs_str = [re.sub(" ", "", x.get()) for x in freq_en]
        latest_errors = {}
        messages = []

        for i in range(len(freq_en)):
            freq_var = freqs_str[i]

            try:  #: Check 1
                freq_int = int(freq_var)
                freqs_int.append(freq_int)

                if not (MAX_VALS_FREQS[0] <= freq_int <= MAX_VALS_FREQS[1]):  #: Check 2
                    args[i] = ("Start frequency" if i == 0 else "End frequency", freq_int, MAX_VALS_FREQS[0],
                               MAX_VALS_FREQS[1])
                    codes[i] = 1
                else:
                    codes[i] = 0

                i += 1

            except ValueError:
                args[i] = (freq_var, 'integer')
                codes[i] = 2

        if len(freqs_int) == 2 and freqs_int[0] > freqs_int[1]:  #: Check 3
            args[2] = ("Start frequency", freqs_int[0], "end frequency", freqs_int[1])
            codes[2] = 3

        for j in range(len(freq_en)):
            code = codes[j]

            if code != 0:
                color = ERROR_COLOR

                if self.props.latest_errors[j] != freqs_str[j]:
                    messages.append((args[j], code))
                    latest_errors[str(j)] = freqs_str[j]
            else:
                color = TEXT_COLOR

            freq_en[j].config(foreground=color)

        if codes[2] != 0:
            freq_en[0].config(foreground=ERROR_COLOR)
            freq_en[1].config(foreground=ERROR_COLOR)

            if self.props.latest_errors[2] != str(hash("#".join(freqs_str))):
                messages.append((args[2], codes[2]))
                latest_errors['2'] = str(hash("#".join(freqs_str)))

        if len(latest_errors):
            self.props.log_messages(messages, latest_errors)

        return codes

    def configure_scale(self, form_validated):
        """Display and set up scale to allow the user to select the number of frequencies.

        1) Determine the maximum number of possible frequencies.
        2) Map the input to actual values according to minimum frequency and compute the number of bits between the
            start and end frequency, if applicable.
        3) Reset the latest errors list tracker to the default.

        Args:
            form_validated (bool): True if the input was validated, False otherwise.

        """
        freqs_str = [re.sub(" ", "", x.get()) for x in [self.start_frequency_en, self.end_frequency_en]]

        if self.state.single_frequency:  #: Step 1
            n_freqs = 1
            lower_bound = bytes.get_binary_limits(int(freqs_str[0]), int(freqs_str[0]), F_MIN)[0]
            upper_bound = None
        else:
            freqs_str = [re.sub(" ", "", x.get()) for x in [self.start_frequency_en, self.end_frequency_en]]
            self.__n_middle_bits = bytes.get_num_middle_bits(int(freqs_str[0]), int(freqs_str[1]), F_MIN)  #: Step 2
            lower_bound, upper_bound = bytes.get_binary_limits(int(freqs_str[0]), int(freqs_str[1]), F_MIN)

            if self.__n_middle_bits > 0:
                n_freqs = self.n_freqs_scale.get()
            else:
                n_freqs = 2

        if form_validated:  #: Step 3
            amplitude_str = re.sub(" ", "", self.amplitude_en.get())
            self.props.clear_latest_errors()
            self.props.on_form_validated(lower_bound, upper_bound, n_freqs, int(amplitude_str))
        else:
            self.props.update_freqs(lower_bound, upper_bound, n_freqs)

    def render(self):
        """Form Component Render method.

        Determine which widgets to show according to the form validation.

        """
        self.fields_frame.place(width=self.width / GOLDEN_RATIO, height=self.height)
        self.other_frame.place(x=self.width / GOLDEN_RATIO, width=self.width / GOLDEN_RATIO ** 2, height=self.height)

        self.single_freq_lb.place(relwidth=1 / GOLDEN_RATIO, relheight=0.25)
        self.single_freq_cb_v.place(relx=1 / GOLDEN_RATIO, relwidth=1 - 1 / GOLDEN_RATIO, relheight=0.25)

        self.start_frequency_lb.place(rely=0.25, relwidth=1 / GOLDEN_RATIO, relheight=0.25)
        self.start_frequency_en.place(rely=0.33, relx=1 / GOLDEN_RATIO, relwidth=1 - 1 / GOLDEN_RATIO)

        if not self.state.single_frequency:
            prefix = 'Start f'
            self.end_frequency_lb.place(rely=0.5, relwidth=1 / GOLDEN_RATIO, relheight=0.25)
            self.end_frequency_en.place(rely=0.57, relx=1 / GOLDEN_RATIO, relwidth=1 - 1 / GOLDEN_RATIO)
        else:
            prefix = 'F'

        self.start_frequency_lb.config(text=('%srequency (mHz):' % prefix))

        self.amplitude_lb.place(rely=0.75, relwidth=1 / GOLDEN_RATIO, relheight=0.25)
        self.amplitude_en.place(rely=0.82, relx=1 / GOLDEN_RATIO, relwidth=1 - 1 / GOLDEN_RATIO)

        self.amplitude_rb_v.place(relx=0.2, relheight=0.25, relwidth=0.6)
        self.amplitude_rb_c.place(relx=0.2, rely=0.2, relheight=0.25, relwidth=0.6)

        #: Custom colors and cursor depending on the GUI's state
        if self.props.is_device_connected and self.props.hive_record_ready:
            state = 'normal'
            cursor = 'xterm'
            highlightbg = 'black'
        else:
            state = 'disabled'
            cursor = 'arrow'
            highlightbg = FG_COLOR

        if self.props.form_validated and not self.state.single_frequency and state == 'normal':
            self.n_freqs_lb.place(relx=0.095, rely=0.5, relwidth=0.7, relheight=0.25)
            self.n_freqs_int.place(rely=0.5, relx=0.78, relheight=0.25)

            if self.__n_middle_bits > 0:
                self.n_freqs_scale.config(to=2 + self.__n_middle_bits)
                self.n_freqs_scale.place(relx=0.1, rely=0.75, relwidth=0.8, relheight=0.25)

            self.props.n_freqs_str_var.set(str(self.props.n_freqs))

        for entry in self.entries:
            entry.config(state=state, cursor=cursor, highlightbackground=highlightbg)

        self.amplitude_rb_c.config(state=state)
        self.amplitude_rb_v.config(state=state)
        self.single_freq_cb_v.config(state=state)
