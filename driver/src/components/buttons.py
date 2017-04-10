"""Buttons Component class definition.

Todo:
    * Dispose of `self.__force_disabled` and replace it by a prop passed down to this component.

.. _src-components-buttons:
    https://github.com/hivebattery/gui/blob/master/driver/src/components/buttons.py

"""
from __future__ import absolute_import

from react.index import Button, GOLDEN_RATIO
from react.component import Component

from src.actions.actions import sBUSY, sDAV
from src.config.config import BG_COLOR


class Buttons(Component):
    """Buttons Component.

    The React Component that contains the GUI's buttons (currently just the Start EIS button).

    Attributes:
        start_eis (react.widget_wrappers.Button): The button to tell the device to begin an EIS session.

    """
    def __init__(self, parent, frame=None, **props):
        """Buttons Component constructor.

        Initializes the only button with the correct parent widget frame and component.

        Args:
            parent (react.component.Component): The component that should contain the buttons.
            frame (react.widget_wrappers.Frame, optional): The Frame where the buttons should be placed. If no frame
                is specified, then the default frame is considered instead.
            **props: The props passed down to the Buttons component.

        """
        super(Buttons, self).__init__(parent, frame, **props)

        self.state = {}

        self.start_eis = Button(self, 'Start EIS', frame=self.parent_frame,
                                command=self.props.on_start_eis, highlightbackground=BG_COLOR, font=("Helvetica", 12))

        self.__force_disabled = False

    @property
    def force_disabled(self):
        """bool: True if all buttons should be disabled regardless of any other factor, False otherwise.
        """
        return self.__force_disabled

    def toggle_force_disable(self):
        """Toggle whether the buttons should be forcibly disabled.

        Changes the value of `self.__force_disabled` to the opposite of its current value and renders this component
        once again.

        """
        self.__force_disabled = not self.__force_disabled
        self.render()

    def render(self):
        """Buttons Component Render method.

        Note: Given that `self.start_eis` is the only button currently in this component, make sure that both the .hive
            file is ready and that the form's input is valid before enabling the button.

        """
        if self.__force_disabled or (hasattr(self.props, 'usb_status') and self.props.usb_status == sBUSY or
                                     self.props.usb_status == sDAV):
            state = 'disabled'
        else:
            state = 'normal'

        if self.props.hive_record_ready and self.props.form_validated:
            self.start_eis.config(state=state)
            self.start_eis.place(relx=0.05, y=1 / GOLDEN_RATIO * self.width - 50, relwidth=0.9, height=self.height)