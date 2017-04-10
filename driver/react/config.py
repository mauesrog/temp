"""React configuration.

Defines certain properties that will affect React's behavior. Furthermore, these parameters are fully customizable
by using the getter and setter functions defined in `react.index`.

.. _React Library:
    https://github.com/hivebattery/gui/blob/master/driver/react/config.py

"""
config = {
    "log": None,
    "def_width": 1000,
    "def_height": 618,
}
"""dict:

React's configuration properties. These are the only properties that are fully implemented by the `__Gui_Controller`,
so adding new properties would have no effect unless `react.index` is modified to reflect these new changes.
"""