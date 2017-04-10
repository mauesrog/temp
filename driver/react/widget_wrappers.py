"""React widgets.

Basically a bunch of Tkinter widgets wrapped around a Meta Class in order to be able to pass and receive
props given any widget that's added to the GUI.

Example:
::
    class ExampleComponent(Component):
        def __init__(self, parent, frame=None, **props):
            super(ExampleComponent, self).__init__(parent, frame, **props)

            self.state = dict(welcome_message='Hello!')

            self.welcome_message_str_var = StringVar()
            self.inner_frame = Frame(self, width=200, height=200, frame=self.parent_frame, bg='gray')
            self.welcome_label = Label(self, self.welcome_message_str_var, frame=self.inner_frame,
                                       font=("Helvetica", 12))
            self.change_message_btn = Button(self, 'Change message', frame=self.inner_frame,
                                             command=self.change_message, font=("Helvetica", 12))

        def change_message(self, e):
            new_msg = 'Goodbye!' if self.state.welcome_message == 'Hello!' else 'Hello!'
            self.set_state(welcome_message=new_msg)

        def render(self):
            self.inner_frame.pack()
            self.welcome_label.pack(side='top')
            self.change_message_btn.pack(side='bottom')

            self.welcome_message_str_var.set(self.state.welcome_message)

Todo:
    * Find a better way to connect the widgets with the components than just accessing the protected
      module variables such as _WIDGETS, _PARENT_FRAME, and _id
    * Condense wrapper.
    * Remove redundant `Mainframe` class.

.. _React Library:
    https://github.com/hivebattery/gui/blob/master/driver/react/widget_wrappers.py

"""
from __future__ import absolute_import

import re
from types import FunctionType
from functools import wraps
import Tkinter as tk
import matplotlib

from .config import config
from .constants import WIDGET_KEY_MAP

matplotlib.use('TkAgg')
matplotlib.rcParams.update({'figure.autolayout': True})

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


_WIDGETS = []
"""list` of :obj:`dict:

Stores references to all Tkinter widgets in he project. Each dict stores both the widget type as defined by
`react.constants` and the widget itself.
"""

_PARENT_FRAME = None
"""Frame: The default parent frame to be used by all widgets that don't have a parent frame defined.
"""

_id = 0
"""int: The widgets' unique id.

Each time a new widget is created, `_id` increases by one so that each widget can be easily identified.
"""

_ids = {}
"""dict` of :obj:`Widget: Maps widgets' hash keys to the actual widget.
"""


def set_parent_frame(v):
    global _PARENT_FRAME
    _PARENT_FRAME = v


def get_widget_id():
    global _id
    curr_id = _id
    _id += 1

    return curr_id


def wrapper(method):
    """Executes before creating an instance `Widget`.

    Some preparation is needed to set up the compatibility of the widgets with `React`. This wrapper
    takes care of that.

    Args:
        method (() -> Any): The method currently being wrapped

    Returns:
        Whatever the original wrapped method would have returned

    """
    @wraps(method)
    def wrapped(*args, **kwargs):
        """The actual wrapper function.

        After evaluating certain conditions, this method takes care of any preparation or
        operation needed by a general purpose React Widget before creation. When the constructor of a class that's an
        instance of `Widget` is called, certain operations happen in the following order, where steps 1-2 are
        pre-rendering operations and steps 4- involve post-rendering operations:

            1) Determine what `Frame` will contain the widget. If `frame` is not in the constructors `kwargs` keys,
                use the default frame.
            2) Given the name of the class that's an instance of `Widget` i.e. `self.__class__.__name__`, run the
                the specific preparation for that class.
            3) The widgets `StringVar`, `IntVar`, and `Menu` are special type of widgets that do not get added
                to `_WIDGETS` and do not get an `id`; nevertheless, all other widgets go through this final step
                where they also get added to their parent component.

        On the other hand, if the method called is `__getattr__`, override normal execution and determine whether
        this widget should be rendered (by adding it to the DoublyLinkedList `self.container.widget_renders`) if
        any of the rendering Tkinter methods `pack`, `place`, or `grid` gets called, or hidden otherwise.

        Args:
            *args: Variable length argument list for the method being wrapped, where `args[0]` is always
                `self` and if the method is `__init__`, `args[1]` is usually the React Component that contains this
                widget.
            **kwargs: Arbitrary keyword arguments

        Returns:
            FunctionType: The wrapped method or the original method depending on the specific behavior
            desired.

        """
        global _PARENT_FRAME
        global _WIDGETS
        self = args[0]
        class_name = self.__class__.__name__
        func_name = method.__name__

        if config['log'] == 2:
            print func_name, args, kwargs

        if func_name == '__init__':
            if 'frame' in kwargs.keys():  #: Step 1
                frame = kwargs['frame']

                if hasattr(frame, 'frame'):
                    frame = frame.frame

                del kwargs['frame']
            else:
                frame = _PARENT_FRAME

            widget = {}

            if class_name == 'Menu':  # Step 2
                self.menu = tk.Menu(frame, **kwargs)
            elif class_name == "StringVar" or class_name == "IntVar":
                self.__setattr__(class_name.lower(), getattr(tk, class_name)())
            elif class_name == "FigureCanvas":
                self._figure_canvas = FigureCanvasTkAgg(args[2], master=frame)
                self.figurecanvas = self._figure_canvas.get_tk_widget()

                widget['widget'] = self.figurecanvas
                widget['type'] = WIDGET_KEY_MAP['figurecanvas']
            else:
                final_kwargs = dict(**kwargs)

                if class_name == "Mainframe":
                    tk_widget = "Frame"
                    tk_args = (args[2],)
                else:
                    tk_widget = class_name
                    tk_args = (frame,)

                    if class_name == "Button" or class_name == "Label" or class_name == "Radiobutton"\
                            or (class_name == "Checkbutton" and args[2] is not None):
                        if class_name == "Label" and not isinstance(args[2], str):
                            final_kwargs['textvariable'] = args[2].stringvar
                        else:
                            final_kwargs['text'] = args[2]
                    elif class_name == "Listbox":
                        final_kwargs['yscrollcommand'] = args[2]
                    elif class_name == "Radiobutton":
                        final_kwargs['variable'] = args[3].intvar
                        final_kwargs['value'] = args[4]
                    elif class_name == "Entry":
                        final_kwargs['textvariable'] = args[2]
                    elif class_name == "Checkbutton":
                        final_kwargs['variable'] = args[3].intvar
                    elif class_name == "Scale" and 'showvalue' not in final_kwargs.keys():
                        final_kwargs['showvalue'] = 0

                self.__setattr__(class_name.lower(), getattr(tk, tk_widget)(*tk_args, **final_kwargs))

                widget['widget'] = getattr(self, class_name.lower())
                widget['type'] = WIDGET_KEY_MAP[class_name.lower()]

            if len(widget) > 0:  #: Step 3
                widget['widget'] = self
                self.container = args[1]

                if hasattr(self.container, 'widgets'):
                    self.container.widgets.insert(self)

                self.id = get_widget_id()
                _WIDGETS.append(widget)

        elif func_name == '__getattr__':
            item = args[1]

            if item == 'pack' or item == 'place' or item == 'grid':
                self.container.widget_renders.insert(self)

        return method(*args, **kwargs)

    return wrapped


class Widget(type):
    """The meta class that wraps the Tkinter widgets.

    """
    def __new__(mcs, class_name, bases, class_dict):
        """ Connects a new Tkinter widget with the `wrapper` method.

        Args:
            class_name (str): The name of the class to be wrapped e.g. 'Frame', 'Mainframe'.
            bases (tuple of object): Parent classes/bases of the meta class
                lines are supported i.e. `(object,)`.
            class_dict (dict): Contains the names of any initial attributes the class should have.

        Source: http://stackoverflow.com/questions/11349183/how-to-wrap-every-method-of-a-class

        """
        new_class_dict = {}
        for attributeName, attribute in class_dict.items():
            if isinstance(attribute, FunctionType):
                attribute = wrapper(attribute)
            new_class_dict[attributeName] = attribute

        new_class_dict['__eq__'] = mcs.eq

        if '__getattr__' not in new_class_dict.keys():
            new_class_dict['__getattr__'] = mcs.getattr

        return type.__new__(mcs, class_name, bases, new_class_dict)

    @staticmethod
    def getattr(self, item):
        """Custom attribute retrieval

        Relieves all attribute retrieval to the actual Tkinter widget, except for 'self.__class__.__name__.lower()',
        which provides direct access to the actual Tkinter widget. Furthermore, this method is responsible
        for rendering component widgets by adding them to the `Component.widget_renders` Doubly Linked List
        (see `react.component`) for more info.

        Args:
            self (Widget): The instance of the class that's an instance of this MetaClass e.g. `Frame`,
                `Entry`.
            item (str): The name of the desired attribute.

        Returns:
            The Tkinter's object attribute if `item` is not 'self.__class__.__name__.lower()', the Tkinter widget itself
                otherwise.

        """
        if item == 'pack' or item == 'place' or item == 'grid':
            self.container.widget_renders.insert(self)

        if item == self.__class__.__name__.lower():
            return getattr(self, item)

        return getattr(getattr(self, self.__class__.__name__.lower()), item)

    @staticmethod
    def eq(self, other):
        """Check for Widget equality.

        Args:
            self (Widget): The instance of the class that's an instance of this MetaClass e.g. `Frame`,
                `Entry`.
            other (Widget): The other instance of a class that's an instance of this MetaClass e.g. `Frame`,
                `Entry`.

        Returns:
            bool: True if the other widget is the same widget, False otherwise.

        """
        try:
            return self.id == other.id
        except AttributeError:
            return False


class StringVar((Widget("StringVar", (object,), {}))):
    """Wrapped `Tkinter.StringVar`

    Attributes:
        stringvar (Tkinter.StringVar): The actual Tkinter `StringVar` object.

    Note:
        * This widget is not added to `_WIDGETS`
        * All attributes of this class are set through the wrapper function.

    """
    def __init__(self):
        """StringVar constructor

        Note:
            The actual initialization happens during `Step 2` of `wrapper.wrapped`.

        """
        pass


class IntVar((Widget("IntVar", (object,), {}))):
    """Wrapped `Tkinter.IntVar`

    Attributes:
        intvar (Tkinter.IntVar): The actual Tkinter `IntVar` object.

    Note:
        * This widget is not added to `_WIDGETS`
        * All attributes of this class are set through the wrapper function.

    """
    def __init__(self):
        """IntVar constructor

        Note:
            The actual initialization happens during `Step 2` of `wrapper.wrapped`.

        """
        pass


class Mainframe((Widget("Mainframe", (object,), {}))):
    """Wrap the `Tkinter.Frame` that serves as the mainframe.

    Attributes:
        mainframe (Tkinter.Frame): The actual Tkinter `Frame` object.

    Note:
        * All attributes of this class are set through the wrapper function.

    """
    def __init__(self, component, root, **kwargs):
        """Mainframe constructor

        Note:
            The actual initialization happens during `Step 2` of `wrapper.wrapped`.

        Args:
            component (Component): The React component that contains this widget.
            root (Tkinter.Tk): Tkinter's Root for the current project.
            **kwargs: Any other properties to pass to the `Tkinter.Frame` constructor.

        """
        pass


class Frame(Widget("Frame", (object,), {})):
    """Wrapped `Tkinter.Frame`.

    Attributes:
        frame (Tkinter.Frame): The actual Tkinter `Frame object.

    Note:
        * All attributes of this class are set through the wrapper function.

    """
    def __init__(self, component, **kwargs):
        """Frame constructor

        Note:
            The actual initialization happens during `Step 2` of `wrapper.wrapped`.

        Args:
            component (Component): The React component that contains this widget.
            **kwargs: Any other properties to pass to the `Tkinter.Frame` constructor.

        """
        pass


class Label(Widget("Label", (object,), {})):
    """Wrapped `Tkinter.Label`.

    Attributes:
        label (Tkinter.Label): The actual Tkinter `Label object.

    Note:
        * All attributes of this class are set through the wrapper function.

    """
    def __init__(self, component, text, **kwargs):
        """Label constructor

        Note:
            The actual initialization happens during `Step 2` of `wrapper.wrapped`.

        Args:
            component (Component): The React component that contains this widget.
            text (str, StringVar): Either a string for the label to display or a `StringVar that will
                most likely change over time.
            **kwargs: Any other properties to pass to the `Tkinter.Label` constructor.

        """
        pass


class Entry(Widget("Entry", (object,), {})):
    """Wrapped `Tkinter.Entry`.

    Attributes:
        entry (Tkinter.Entry): The actual Tkinter `Entry object.

    Note:
        * All attributes of this class are set through the wrapper function.

    """
    def __init__(self, component, str_var, **kwargs):
        """Label constructor

        Note:
            The actual initialization happens during `Step 2` of `wrapper.wrapped`.

        Args:
            component (Component): The React component that contains this widget.
            str_var (StringVar): A `StringVar that will change as soon as the user types and will store
                that dynamic value.
            **kwargs: Any other properties to pass to the `Tkinter.Label` constructor.

        """
        pass

    def is_empty(self):
        """Check if Entry is empty.

        Uses a regular expression to check for an empty entry.

        Returns:
            bool: True if the entry is empty or made up of only white spaces, False otherwise.

        """
        return bool(re.search('^ *$', self.get()))


class Scale(Widget("Scale", (object,), {})):
    """Wrapped `Tkinter.Scale`.

    Attributes:
        scale (Tkinter.Scale): The actual Tkinter Scale object.

    Note:
        * All attributes of this class are set through the wrapper function.

    """
    def __init__(self, component, **kwargs):
        """Scale constructor

        Note:
            The actual initialization happens during `Step 2` of `wrapper.wrapped`.

        Args:
            component (Component): The React component that contains this widget.
            **kwargs: Any other properties to pass to the `Tkinter.Scale` constructor.

        """
        pass


class Button(Widget("Button", (object,), {})):
    """Wrapped `Tkinter.Button`.

    Attributes:
        button (Tkinter.Button): The actual Tkinter Button object.

    Note:
        * All attributes of this class are set through the wrapper function.

    """
    def __init__(self, component, text, **kwargs):
        """Button constructor

        Note:
            The actual initialization happens during `Step 2` of `wrapper.wrapped`.

        Args:
            component (Component): The React component that contains this widget.
            text (str): The button will display this string.
            **kwargs: Any other properties to pass to the `Tkinter.Button` constructor.

        """
        pass


class Scrollbar(Widget("Scrollbar", (object,), {})):
    """Wrapped `Tkinter.Scrollbar`.

    Attributes:
        scrollbar (Tkinter.Scrollbar): The actual Tkinter Scrollbar object.

    Note:
        * All attributes of this class are set through the wrapper function.

    """
    def __init__(self, component, **kwargs):
        """Scrollbar constructor

        Note:
            The actual initialization happens during `Step 2` of `wrapper.wrapped`.

        Args:
            component (Component): The React component that contains this widget.
            **kwargs: Any other properties to pass to the `Tkinter.Scrollbar` constructor.

        """
        pass


class Listbox(Widget("Listbox", (object,), {})):
    """Wrapped `Tkinter.Listbox`.

    Attributes:
        listbox (Tkinter.Listbox): The actual Tkinter Listbox object.

    Note:
        * All attributes of this class are set through the wrapper function.

    """
    def __init__(self, component, yscrollcommand, **kwargs):
        """Listbox constructor

        Note:
            The actual initialization happens during `Step 2` of `wrapper.wrapped`.

        Args:
            component (Component): The React component that contains this widget.
            yscrollcommand (() -> None): The function bound to the `set` attribute of a `Scrollbar`
            **kwargs: Any other properties to pass to the `Tkinter.Scrollbar` constructor.

        """
        pass


class Radiobutton(Widget("Radiobutton", (object,), {})):
    """Wrapped `Tkinter.Radiobutton`.

    Attributes:
        radiobutton (Tkinter.Radiobutton): The actual Tkinter Radiobutton object.

    Note:
        * All attributes of this class are set through the wrapper function.

    """
    def __init__(self, component, text, variable, value, **kwargs):
        """Radiobutton constructor

        Note:
            The actual initialization happens during `Step 2` of `wrapper.wrapped`.

        Args:
            component (Component): The React component that contains this widget.
            text (str): The label to be displayed next to the radiobutton.
            variable (IntVar): Will store the radiobutton's current value (1 if the radiobutton is selected, 0
                otherwise).
            value (int): The radiobutton's initial value (1 if the radiobutton is selected, 0 otherwise).
            **kwargs: Any other properties to pass to the `Tkinter.Radiobutton` constructor.

        """
        pass


class Checkbutton(Widget("Checkbutton", (object,), {})):
    """Wrapped `Tkinter.Checkbutton`.

    Attributes:
        checkbutton (Tkinter.Checkbutton): The actual Tkinter Checkbutton object.

    Note:
        * All attributes of this class are set through the wrapper function.

    """
    def __init__(self, component, text, variable, value, **kwargs):
        """Checkbutton constructor

        Note:
            The actual initialization happens during `Step 2` of `wrapper.wrapped`.

        Args:
            component (Component): The React component that contains this widget.
            text (str, optional): The label to be displayed next to the checkbutton. None means no text will be
                displayed.
            variable (IntVar): Will store the checkbutton's current value (1 if the checkbutton is toggled, 0
                otherwise).
            value (int): The checkbutton's initial value (1 if the checkbutton should be initially toggled,
                0 otherwise).
            **kwargs: Any other properties to pass to the `Tkinter.Radiobutton` constructor.

        """
        pass


class FigureCanvas(Widget("FigureCanvas", (object,), {})):
    """Wrapped matplotlib's implementation of `Tkinter.FigureCavnas` i.e. `FigureCanvasTkAgg`.

    This implementation only allows displaying a graph.

    Attributes:
        _figure_canvas (Matplotlib.backends.backend_tkagg.FigureCanvasTkAgg): Matplotlib's object containing a
            Tkinter.FigureCavnas instance.
        figurecanvas (Tkinter.FigureCanvas): The actual Tkinter FigureCanvas object.

    Note:
        * All attributes of this class are set through the wrapper function.

    """
    def __init__(self, component, fig, **kwargs):
        """FigureCanvas constructor

        Note:
            The first part of the initialization happens during `Step 2` of `wrapper.wrapped`.

        Args:
            component (Component): The React component that contains this widget.
            fig (Matplotlib.figure): The graph to display
            **kwargs: Any other properties to configure the `Tkinter.FigureCanvas` instance.

        """
        if len(kwargs):
            self.figurecanvas.config(**kwargs)

    def plot_show(self):
        """Passthrough for matplotlib's `FigureCanvasTkAgg.show` method

        """
        self._figure_canvas.show()

    def __getattr__(self, item):
        """Special attribute retrieval

        Since `FigureCanvas` contains instances of both matplotlib's `FigureCanvasTkAgg` and `Tkinter.FigureCanvas`,
        some extra work is required to determine whose attribute should be fetched.

        Args:
            item (str): The name of the desired attribute.

        Returns:
            The `FigureCanvasTkAgg` attribute if it exists, the `Tkinter.FigureCanvas` attribute if `item` is not
                '_figure_canvas', or the `Tkinter.FigureCanvas` instance itself otherwise.

        """
        if item == '_figure_canvas':
            return getattr(self, item)

        if hasattr(self._figure_canvas, item):
            return getattr(self._figure_canvas, item)

        return getattr(self.figurecanvas, item)


class Menu(Widget("Menu", (object,), {})):
    """Wrapped `Tkinter.Menu`.

    Attributes:
        menu (Tkinter.Menu): The actual Tkinter Menu object.

    Note:
        * All attributes of this class are set through the wrapper function.

    """
    def __init__(self, component, **kwargs):
        """Menu constructor

        Note:
            The actual initialization happens during `Step 2` of `wrapper.wrapped`.

        Args:
            component (Component): The React component that contains this widget.
            **kwargs: Any other properties to pass to the `Tkinter.Menu` constructor.

        """
        pass
