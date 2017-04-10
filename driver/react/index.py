"""React. Main module.

This is React's main file, and it controls the react/redux data flow for any given project with the
private class `__GuiController` and the public methods that provide access to the class.

Note:
    The `__GuiController` should only be initialized once in the main component's constructor by calling
    this module's `set_app` right after the call to the component's `super`.

Example:
::
    import react.index as react
    from react.component import Component

    WIDTH = 1000
    HEIGHT = WIDTH / react.GOLDEN_RATIO

    class GUI(Component):
        def __init__(self):
            react.config('log', LOG)

            react.new_root(WIDTH, HEIGHT, center=True, resizable=(False, False), title='Hive Battery',
                           bg="black")

            ...  #: Calls specific to the Component class, except the call to `super` (see `react.component` for
                    specific details)
            super(...)  #: Call to super with the requried params (see `react.component` for
                           specific details)

            react.set_app(self)

.. seealso:: :py:mod:`react-component`

Todo:
    * Find a better way to handle the private class without using passthrough functions.
    * There's a problem bringing the window to the front in MacOS, even with the bash script
    * Provide functionality to set up more than one background click event

.. _react.index:
    https://github.com/hivebattery/gui/blob/master/driver/react/index.py

"""
from __future__ import absolute_import

import subprocess
from sys import platform
import numpy as np
from tkFileDialog import askdirectory as AskDirectory
from Tkinter import Tk as Root

from .constants import *
from .widget_wrappers import Mainframe, Frame, Label, Entry, Button, Scale, Scrollbar, Listbox, StringVar, \
    IntVar, Radiobutton, Checkbutton, FigureCanvas, _WIDGETS, Menu
from Tkinter import N, S, W, E, HORIZONTAL, END
from .config import config as __config
from .data_structures.named_tuple import NamedTuple

GOLDEN_RATIO = (1 + 5 ** 0.5) / 2
"""float: Approx. 1.618. Useful to create proportional widgets.
"""

__GUI_CONTROLLER = None
""":obj:`__GuiController`

The instance of `__GuiController`that will be used during the entire execution of the GUI's mainloop.
"""

_EVENT_TYPES = ["<KeyPress>", "<KeyRelease>", "<ButtonPress>", "<ButtonRelease>", "<Motion>", "<Enter>",
                "<Leave>", "<FocusIn>", "<FocusOut>", "<Expose>", "<Visibility>", "<Destroy>","<Unmap>", "<Map>",
                "<Reparent>", "<Configure>", "<Gravity>", "<Circulate>", "<Property>", "<Colormap>",
                "<Activate>", "<Deactivate>", "<MouseWheel>"]
""":obj:`list` of :obj:`str`

Contains most of Tkinter's event names.
"""


def new_root(width=__config['def_width'], height=__config['def_height'], center=False, resizable=(False, False),
             title='New project', bg='white', logging_on=False, **kwargs):
    """Instantiate `__Gui_Controller`

    This method should only be called once at the beginning of the constructor, as shown in the `Example` section of
    this module's docstring.

    Note:
        See the `Args` section of `__GuiController` for more information. Although the args do not appear to be
        optional in the constructor of `__GuiController`, this method handles the optional parameters and
        sets them to a default value if the key was not specified when calling this mehtod.

    Returns:
        __GuiController: A new instance to control the GUI.

    """
    global __GUI_CONTROLLER
    __GUI_CONTROLLER = __GuiController(width, height, center, resizable, title, bg, logging_on, **kwargs)


def get_mainframe():
    """Mainframe getter

    Provides access to the private property `__GUI_CONTROLLER.mainframe` i.e. the window's mainframe.

    Note:
        See `__GUI_CONTROLLER.mainframe` for more information.

    Returns:
        react.widget_wrappers.Frame: The mainframe.

    """
    return __GUI_CONTROLLER.mainframe


def get_root():
    """Root getter

    Provides access to the private property `__GUI_CONTROLLER.root` i.e. Tkinter's `Root`.

    Note:
        See `__GUI_CONTROLLER.root` for more information.

    Returns:
        Tkinter.Tk: Tkinter's Root.

    """
    return __GUI_CONTROLLER.root


def get_top_menu():
    """Menu getter

    Provides access to the private property `__GUI_CONTROLLER.menu`.

    Note:
        See `__GUI_CONTROLLER.menu` for more information.

    Returns:
        Tkinter.Menu: The top menu.

    """
    return __GUI_CONTROLLER.menu


def add_submenu(submenu, title):
    """Menu setter.

    Provides access to set the private property `__GUI_CONTROLLER.menu`.

    Note:
        See `__GUI_CONTROLLER.menu` for more information.

    """
    __GUI_CONTROLLER.menu = dict(submenu=submenu.menu, title=title)


def set_logging(log):
    """Log setter

    Provides access to the private property `__GUI_CONTROLLER.log`.

    Note:
        See `__GUI_CONTROLLER.log` for more information.

    """
    __GUI_CONTROLLER.log = log


def add_event_handler(event, handler, key, active=False):
    """Custom root event handlers insertion.

    Adds a new handler to be triggered whenever the specified event happens at a `Root` level.

    Args:
        event (str): Tkinter's exact event name to be bound to Root
        handler ((Tkinter.Event) -> None): The method to be triggered when the event happens.
        key (str): A UNIQUE key to identify this handler. The user needs to make sure that this key is truly unique,
            since it will be used to activate, deactivate, and trigger the handler.
        active (bool): True if the handler should be initially activated to handle the event or False otherwise.

    """
    __GUI_CONTROLLER.event_handlers[event][key] = dict(handler=handler, active=active)


def set_active_event_handler(event, key, active):
    """Activate root custom event handler.

    Adds a new handler to be triggered whenever the specified event happens at a `Root` level.

    Args:
        event (str): Tkinter's exact event name already bound to Root.
        key (str): The unique handler key.
        active (bool): True if the handler should be active to respond to the event or False otherwise.

    """
    __GUI_CONTROLLER.event_handlers[event][key]['active'] = active


def config(**kwargs):
    """`react.config` setter.

    Update config properties.

    Args:
        **kwargs: The config keys and their new values.

    """
    for key, val in kwargs.items():
        __config[key] = val


def cget(key):
    """`react.config` getter.

    Check the a current config value.

    Args:
        key (str): The key of the target config property.

    Returns:
        The config value for that key.

    """
    return __config[key]


def set_timeout(mseconds, callback):
    """Set a timeout with `Tkinter.after` (after certain milliseconds).

    Set a function to be called after a timeout has passed.

    Args:
        mseconds: Milliseconds to wait before triggering the callback.
        callback: The function to be called after the specified milliseconds have passed.

    Returns:
        Tkinter.after: The alarm identifier the event to allow for cancellation with `Tkinter.after_cancel`

    """
    return __GUI_CONTROLLER.root.after(mseconds, callback)


def set_immediate(callback):
    """Set a timeout with `Tkinter.after` (immediately).

    Set a function to be called right after Tkinter can handle a new operation.

    Args:
       callback (() -> None): The function to be called after when Tkinter's ready.

    Returns:
       Tkinter.after: The alarm identifier the event to allow for cancellation with `Tkinter.after_cancel`

    """
    return set_timeout(0, callback)


def set_app(app):
    """Passthrough for `__GUI_CONTROLLER.set_app`

    Provides access to the private method `__GUI_CONTROLLER.set_app`.

    Note:
        See `__GUI_CONTROLLER.set_app` for more information.

    """
    __GUI_CONTROLLER.app = app


def set_up_background_click_event(exclude_type, bg_callback):
    """Passthrough for `__GUI_CONTROLLER.set_app`

    Provides access to the private method `__GUI_CONTROLLER.set_up_background_click_event`.

    Note:
        See `__GUI_CONTROLLER.set_up_background_click_event` for more information.

    """
    __GUI_CONTROLLER.set_up_background(exclude_type, bg_callback)


def set_close_window_handler(handler):
    """Passthrough for `__GUI_CONTROLLER.set_close_window_handler`

   Provides access to the private method `__GUI_CONTROLLER.set_close_window_handler`.

   Note:
       See `__GUI_CONTROLLER.set_close_window_handler` for more information.

   """
    __GUI_CONTROLLER.set_close_window_handler(handler)


def setroot_geometry(width, height, center=False):
    """Passthrough for `__GUI_CONTROLLER.setroot_geometry`

    Provides access to the private method `__GUI_CONTROLLER.setroot_geometry`.

    Note:
       See `__GUI_CONTROLLER.setroot_geometry` for more information.

    """
    __GUI_CONTROLLER.setroot_geometry(width, height, center)


def widgets_ready():
    """Passthrough for `__GUI_CONTROLLER.widgets_ready`

    Provides access to the private method `__GUI_CONTROLLER.widgets_ready`.

    Note:
       See `__GUI_CONTROLLER.widgets_ready` for more information.

    """
    __GUI_CONTROLLER.widgets_ready()


class __GuiController(object):
    """GUI and Tkinter's `Root` controller

    This class most be exclusively controlled by the public, passthrough methods defined above.

    Attributes:
        root (Tkinter.Tk): Tkinter's Root (master).
        title (str): The title to display at the top of the window.
        bg_color (str): The background color for all widgets with no color specified and also for the mainframe.
        mainframe_props (dict): The Tkinter properties of `self.mainframe` (not related to `React` props).
        event_handlers (dict of (dict of (dict of (bool, (Tkinter.Event) -> None)))): This dict contains an inner dict
            for each Tkinter event included in `_EVENT_TYPES`, which will be bound to `self.root`. Moreover, each inner
            dict contains a dict for each event with exactly two keys: `active` defines whether the event handler is
            active and should be called when the event happens, and `handler` defines the actual function to be
            called to handle that particular event.

    """
    def __init__(self, width, height, center, resizable, title, bg, logging_on, **kwargs):
        """ `__GuiController` __init__ method.

        Args:
            width (int, optional): The width of the window (mainframe). The default width is specified in module
                `react.config`.
            height (int, optional): The height of the window (mainframe). The default height is specified in module
                `react.config`.
            center (bool, optional): Whether the window should be centered. Default is false.
            resizable (tuple of bool, optional): Two parameters that toggle whether the window is
                resizable horizontally and vertically (the booleans should be in that order i.e. (x, y))
            title (str, optional): `self.title`. Default is 'New project'.
            bg (str, optional): `self.bg_color`. Default is 'white'.
            logging_on (bool, optional): `self.log`. Default is no logging.
            **kwargs: Any other Tkinter props that should be passed to `self.mainframe`.

        """
        self.root = Root()
        self.title = title
        self.bg_color = bg
        self.mainframe_props = dict(bg=bg, width=width, heigh=height, **kwargs)
        self.event_handlers = {}

        self.__app = None
        self.__mainframe = None
        self.__menu = None
        self.__log = logging_on

        self.__root_displayed = False

        self.config_geom(width, height, resizable, center)

    @property
    def app(self):
        """Component: GUI's main component."""
        return self.__app

    @app.setter
    def app(self, value):
        self.__app = value

        self.mainframe = Mainframe(self.app, self.root, **self.mainframe_props)

    @property
    def mainframe(self):
        """react.widget_renders.Frame: GUI's `Frame` that will contain all other widgets."""
        return self.__mainframe

    @mainframe.setter
    def mainframe(self, value):
        self.__mainframe = value
        self.__mainframe.pack()

    @property
    def menu(self):
        """react.widget_renders.Menu:

        The menu to show at the top of the window. The getter creates the topmost menu,
        and the setter adds a submenu (e.g. 'File', 'Edit').
        """
        if self.__menu is None:
            self.__menu = Menu(self.root).menu

        return self.__menu

    @menu.setter
    def menu(self, value):
        if self.__menu is not None:
            self.__menu.add_cascade(label=value['title'], menu=value['submenu'])
            self.root.config(menu=self.menu)

    @property
    def log(self):
        """bool: True if `React` should log what's happening or False otherwise.
        """
        return self.__log

    @log.setter
    def log(self, value):
        self.__log = value

    def config_geom(self, width, height, resizable, center):
        """`Root` config.

        This is the order of the operations:
            1) Set the root's alpha to 0 (makes it invisible), so that the setup can happen without the user
                seeing all these unaesthetic changes.
            2) Configure the root's appeareance properties i.e. title, bg, resizable, width, height, and center.
            3) Set up the event handlers.

        Args:
            width (int): The width of the window (mainframe).
            height (int): The height of the window (mainframe).
            center (bool): Whether the window should be centered. Default is false.
            resizable (tuple of bool): Two parameters that toggle whether the window is resizable horizontally and
                vertically (the booleans should be in that order i.e. (x, y))

        """
        self.root.attributes("-alpha", 0.0)  #: Step 1

        self.root.title(self.title)  #: Step 2
        self.root.configure(background=self.bg_color)

        if resizable is not None:
            self.root.resizable(*resizable)

        if width and height:
            self.setroot_geometry(width, height, center)

        for event_type in _EVENT_TYPES:  #: Step 3
            self.event_handlers[event_type] = {}
            self.root.bind(event_type, self.handle_event)

    def widgets_ready(self):
        """Display all widgets.

        Once the root's setup is taken care of, this method moves the root window to the front and makes it
        visible again.

        """
        if not self.__root_displayed:
            self.__root_displayed = True
            self.root.lift()

            if platform == 'darwin':  #: Special way to move the window to the front for MacOS
                subprocess.call("./scripts/bash/bringtofront.sh", shell=True)

            self.root.attributes("-alpha", 1.0)

    def setroot_geometry(self, w, h, center):
        """`Root` dimensions and position.

        Define the size of the window and whether it should be centered.

        Args:
            w (int): The width of the window (mainframe).
            h (int): The height of the window (mainframe).
            center (bool): Whether the window should be centered. Default is false.

        """
        ws = self.root.winfo_screenwidth()
        hs = self.root.winfo_screenheight()

        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)

        size_code = '%dx%d' % (w, h)

        if center:
            size_code += '+%d+%d' % (x, y)

        self.root.geometry(size_code)

    def set_close_window_handler(self, handler):
        """`Root` destroy handler.

        Set up a handler to be called as soon as the user clicks the close window button.

        Args:
            handler (() -> None): The function that will handle the closing of the window.

        """
        self.root.protocol("WM_DELETE_WINDOW", lambda: self.on_close_window(handler))

    def set_up_background(self, exclude_type, bg_callback):
        """Trigger a callback after clicking outside of a widget.

        Given a target widget and its type, set up all other widgets so that whenever the user clicks on them,
        a handler is triggered.

        Args:
            exclude_type (int): The numerical code of the target widget as defined in `react.constants`.
            bg_callback (() -> None): The function that all widgets, except for the target widget, should execute
                whenever clicked.

        """
        self.mainframe.bind("<Button-1>", lambda e: self.on_bg_click(bg_callback))

        for widget in _WIDGETS:
            if widget['type'] != exclude_type:
                widget['widget'].bind("<Button-1>", lambda e: self.on_bg_click(bg_callback))

    def handle_event(self, e):
        """Handle root events.

        Assuming `self.config_geom` has bound all events to `self.root`, this method gets called every time
        any of those events happen. However, nothing will happen unless the user has already defined and activated
        a with `add_event_handler` and/or `set_active_event_handler`, in which case all bound events are triggered.

        Args:
            e (Tkinter.Event): The event object with a `type` attribute that serves as a key to fetch a value
             from `EVENT_KEY_MAP` as defined in `react.constants`.

        """
        for handler in self.event_handlers[EVENT_KEY_MAP[int(e.type)]].values():
            if handler['active']:
                self.root.after_idle(lambda: handler['handler'](e))

    def on_close_window(self, handler):
        """Close window event.

        When the user clicks the close window button, the custom handler set with `self.set_close_window_handler` gets
        executed, and finally, the root is destroyed and the window closed.

        Args:
            handler (() -> None): The handler passed as a param to `self.set_close_window_handler`.

        """
        handler()
        self.root.destroy()

    def on_bg_click(self, callback):
        """Background click event.

        First, the root steals focus from whichever widget had it before, and assuming the user defined a valid
        `callback` with `self.set_up_background`, that callback gets called.

        Args:
            callback (() -> None): The callback passed as a param to `self.set_up_background`.

        """
        self.root.focus()
        callback()
