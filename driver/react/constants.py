"""React constants.

The react widgets and the main react GUI controller file, `<index.py>`, need
these constant definitions, some are protected ans others public.

Todo:
    * ...

.. _React Library:
    https://github.com/hivebattery/gui/blob/master/driver/react/constants.py

"""
LABEL = 0
"""int: Tkinter's `Label` widget code.
"""

ENTRY = 1
"""int: Tkinter's `Entry` widget code.
"""

STRING_VAR = 2
"""int: Tkinter's `StringVar` widget code.
"""

SCALE = 3
"""int: Tkinter's `Scale` widget code.
"""

FRAME = 4
"""int: Tkinter's `Frame` widget code.
"""

BUTTON = 5
"""int: Tkinter's `Button` widget code.
"""

SCROLLBAR = 6
"""int: Tkinter's `Scrollbar` widget code.
"""

LISTBOX = 7
"""int: Tkinter's `Listbox` widget code.
"""

RADIOBUTTON = 8
"""int: Tkinter's `Radiobutton` widget code.
"""

CHECKBUTTON = 9
"""int: Tkinter's `Checkbutton` widget code.
"""

FIGURECANVAS = 10
"""int: Tkinter's `FigureCanvasTkAgg` widget code.
"""

MENU = 11
"""int: Tkinter's `Menu` widget code.
"""

WIDGET_KEY_MAP = {
    "mainframe": FRAME,
    "label": LABEL,
    "entry": ENTRY,
    "stringvar": STRING_VAR,
    "scale": SCALE,
    "frame": FRAME,
    "button": BUTTON,
    "scrollbar": SCROLLBAR,
    "listbox": LISTBOX,
    "radiobutton": RADIOBUTTON,
    "checkbutton": CHECKBUTTON,
    "figurecanvas": FIGURECANVAS,
    "menu": MENU,
}
"""dict of int: Maps explicit widget names to widget types.
"""

EVENT_KEY_MAP = {
    2: "<KeyPress>",
    3: "<KeyRelease>",
    4: "<ButtonPress>",
    5: "<ButtonRelease>",
    6: "<Motion>",
    7: "<Enter>",
    8: "<Leave>",
    9: "<FocusIn>",
    10: "<FocusOut>",
    12: "<Expose>",
    15: "<Visibility>",
    17: "<Destroy>",
    18: "<Unmap>",
    19: "<Map>",
    21: "<Reparent>",
    22: "<Configure>",
    24: "<Gravity>",
    26: "<Circulate>",
    28: "<Property>",
    32: "<Colormap>",
    36: "<Activate>",
    37: "<Deactivate>",
    38: "<MouseWheel>"
}
"""dict of str: Maps Tkinter's event codes to explicit names.
"""