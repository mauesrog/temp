"""Main Dashboard Component class definition.

.. _src-components-main_dashboard:
    https://github.com/hivebattery/gui/blob/master/driver/src/components/main_dashboard.py

"""
from __future__ import absolute_import

from react.component import Component
from react.index import Frame, Label, StringVar

from src.config.config import BG_COLOR, TEXT_COLOR
from src.components.plot import Plot


class MainDashboard(Component):
    """MainDashboard Component.

    The React Component that contains either the GUI's plot or a waiting screen if the device is not connected or the
    .hive file is not ready.

    Attributes:
        status (react.widget_wrappers.StringVar): Stores the current title of the main dashboard.
        dashboard (react.widget_wrappers.Frame): The frame where all main widgets will be contained.
        label (react.widget_wrappers.Label): The title of the dashboard.
        nyquist_plot (src.components.plot.Plot): The Nyquist Plot generated by the data returned by the EIS.

    """
    def __init__(self, parent, **props):
        """Main Dashboard Component constructor.

        Args:
            parent (react.component.Component): The component that should contain the main dashboard.
            frame (react.widget_wrappers.Frame, optional): The Frame where the main dashboard should be placed. If no
                frame is specified, then the default frame is considered instead.
            **props: The props passed down to the MainDashboard component.

        """
        super(MainDashboard, self).__init__(parent, **props)

        self.state = {}

        self.status = StringVar()

        self.dashboard = Frame(self, bg=BG_COLOR, frame=self.parent_frame, width=self.width, height=self.height)
        self.label = Label(self, self.status, frame=self.dashboard, bg=BG_COLOR, foreground=TEXT_COLOR,
                           font=("Helvetica", 30))
        self.nyquist_plot = Plot(self, frame=self.dashboard, width=self.width, height=self.height,
                                 x=self.x, y=0, data=self.props.data, freqs_explicit=self.props.freqs_explicit)

    def render(self):
        """Main Dashboard Component Render method.

        Render the Nyquist Plot if both the .hive file is ready and the device is connected. Otherwise, render a waiting
        screen indicating what's left to be done.

        """
        self.dashboard.pack(side='right', fill='y', padx=(1, 0))

        if self.props.is_device_connected and self.props.hive_record_ready:
            title = "Nyquist Plot"

            self.nyquist_plot.render()
        else:
            title = 'Loading user data...' if self.props.is_device_connected else 'No device detected'

        self.label.place(relwidth=1, height=100)
        self.status.set(title)