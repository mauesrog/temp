"""Console Component class definition.

Todo:
    * Provide a better and smoother scrolling experience.

.. _src-components-console:
    https://github.com/hivebattery/gui/blob/master/driver/src/components/console.py

"""
from __future__ import absolute_import

from react.index import Frame, Scrollbar, Listbox, END
from react.component import Component

from src.common.log.console_message import log_message
from src.config.config import FG_COLOR

CONSOLE_PADDING = 3
"""int: Defines how much the console should pad each message logged.
"""
MAX_CHARS_CONSOLE = 20
"""int: Defines the the maximum number of characters allowed per line.
"""


class Console(Component):
    """Console Component.

    The React Component that contains the GUI's console, which logs all relevant information for the user.

    Attributes:
        console_fr (react.widget_wrappers.Frame): The bounding box for the console that contains all messages.
        console_sc (react.widget_wrappers.Scrollbar): Allows for scrolling up and down the console messages.
        console_li (react.widget_wrappers.Listbox): The actual container of the list of all messages.

    """
    def __init__(self, parent, frame=None, **props):
        """Console Component constructor.

        Args:
            parent (react.component.Component): The component that should contain the console.
            frame (react.widget_wrappers.Frame, optional): The Frame where `self.console_fr` should be placed. If no
                frame is specified, then the default frame is considered instead.
            **props: The props passed down to the Console component.

        """
        super(Console, self).__init__(parent, frame, **props)

        self.state = {}

        self.console_fr = Frame(self, frame=self.parent_frame, bg='gray', width=self.width, height=self.height,
                                bd=0)
        self.console_sc = Scrollbar(self, frame=self.console_fr)
        self.console_li = Listbox(self, self.console_sc.set, frame=self.console_fr, bg=FG_COLOR, bd=0)

    def display_messages(self):
        """Displays new messages and appends them to the Listbox.

        Given a list of tuple made up of messages and message codes, these operations happen in the follwoing order:

            1) Check that there is at least one new message.
            2) Generate `ConsoleMessage` instances from each new messages.
            3) Append each new message to the listbox with its corresponding color.
            4) Scroll down to the newest message.
            5) Mark these new messages as processed.

        """
        new_console_msgs = self.props.new_msgs

        save_msgs = []

        if len(new_console_msgs) > 0:  #: Step 1
            for args, code in new_console_msgs:
                msg_obj = log_message(args, code, MAX_CHARS_CONSOLE)  #: Step 2

                for msg in msg_obj:
                    save_msgs.append(msg)
                    padding = "".join([" " for i in range(CONSOLE_PADDING)])

                    self.console_li.insert(END, padding + msg.message + padding)  #: Step 3
                    self.console_li.itemconfig(self.console_li.size() - 1, {"bg": msg.color})

            self.console_li.see("end")  #: Step 4
            self.props.clear_new_msgs()

        self.console_sc.config(command=self.console_li.yview)

        if len(save_msgs) > 0:  #: Step 5
            self.props.update_console_messages(save_msgs)
            self.console_fr.update()

    def render(self):
        """Console Component Render method.

        """
        self.console_fr.pack(side='top', pady=(0, 1))

        self.console_sc.place(relwidth=1, relheight=1)
        self.console_li.place(relwidth=1, relheight=1)

        self.display_messages()
