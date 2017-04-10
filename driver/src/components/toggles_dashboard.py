"""Toggles Dashboard Component class definition.

.. _src-components-toggles_dashboard:
    https://github.com/hivebattery/gui/blob/master/driver/src/components/toggles_dashboard.py

"""
from __future__ import absolute_import

from react.index import Frame, set_up_background_click_event, ENTRY
from react.component import Component

from src.components.form import Form
from src.components.buttons import Buttons
from src.config.config import BG_COLOR


class TogglesDashboard(Component):
    """TogglesDashboard Component.

    The React Component that groups the GUI's Form and Buttons components and passes down props from the main component
    down to both components.

    Attributes:
        status (react.widget_wrappers.StringVar): Stores the current title of the main dashboard.
        dashboard (react.widget_wrappers.Frame): The frame where the form and buttons will be contained.
        form (src.components.form.Form): The GUI's form.
        buttons (src.components.buttons.Buttons): The GUI's buttons.

    See Also:
        Components :py:mod:`src-components-form` and :py:mod:`src-components-buttons`.

    """
    def __init__(self, parent, frame=None, **props):
        """ToggleDashboard Component constructor.

        Args:
           parent (react.component.Component): The component that should contain the toggles dashboard.
           frame (react.widget_wrappers.Frame, optional): The Frame where the toggles dashboard should be placed. If no
               frame is specified, then the default frame is considered instead.
           **props: The props passed down to the toggles dashboard component (and thus to both the Form and
            Buttons components).

        """
        super(TogglesDashboard, self).__init__(parent, frame, **props)

        self.state = {}

        self.dashboard = Frame(self, width=self.width, height=self.height, bg=BG_COLOR, frame=self.parent_frame)

        self.form = Form(self, self.dashboard, width=self.width, height=self.height - 50,
                         toggle_form=self.props.toggle_form, form_validated=self.props.form_validated,
                         latest_errors=self.props.latest_errors, on_form_validated=self.props.on_form_validated,
                         update_freqs=self.props.update_freqs, log_messages=self.props.log_messages,
                         n_freqs_str_var=self.props.n_freqs_str_var, n_freqs=self.props.n_freqs,
                         amplitude_str_var=self.props.amplitude_str_var, amplitude_int_var=self.props.amplitude_int_var,
                         clear_latest_errors=self.props.clear_latest_errors,
                         update_latest_errors=self.props.update_latest_errors,
                         poll_history=lambda key, d: self.props.poll_history(key, d),
                         is_device_connected=self.props.is_device_connected,
                         hive_record_ready=self.props.hive_record_ready)

        self.buttons = Buttons(self, self.dashboard, width=self.width, height=50,
                               form_validated=self.props.form_validated, on_start_eis=self.props.on_start_eis,
                               on_stop_eis=self.props.on_start_eis, usb_error=self.props.usb_error,
                               usb_status=self.props.usb_status, change_default_path=self.props.change_default_path,
                               hive_record_ready=self.props.hive_record_ready,
                               attempted_write=self.props.attempted_write, init_hive_record=self.props.init_hive_record,
                               error_default_path=self.props.error_default_path, columnspan=self.props.columnspan)

    def component_will_mount(self):
        """Overrides Component's `component_will_mount`.

        If this is the first time this component is rendered after having been hidden, set up a background click event
        to blur the form's entries.

        See Also:
            Form component :py:mod:`src-components-form`.

        """
        set_up_background_click_event(ENTRY, self.form.on_bg_click)

    def render(self):
        """Toggles Dashboard Component Render method.

        """
        self.dashboard.pack(side='bottom')

        self.form.render()
        self.buttons.render()
