"""React components.

This is the "interface" that all components will implement. The three special public methods,
render, component_will_receive_props, and component_will_mount, are meant to be overridden by the
component that implements this interface, otherwise nothing might be displayed since the methods defined
in this class are nothing more than placeholders. You can find concrete examples in the actual Component
class definition.

Todo:
    * Find a better way to handle component identification and comparison.
    * Pass props when calling `component_will_mount`.
    * Make sure the DoublyLinkedList is actually necessary to implement this `React` behavior.
    * Make sure the `wrapper` operation flow and precedence  is in line with real `React` (this could
        potentially lead to non-React behavior that's difficult to debug)
    * Verify if letting the user decide exactly when to pass props is a bad idea.

.. _react-component:
    https://github.com/hivebattery/gui/blob/master/driver/react/components.py

"""
from __future__ import absolute_import

from functools import wraps
from types import FunctionType
import numpy as np

from .data_structures.doubly_linked_list import DoublyLinkedList
from .redux.index import *
from .config import config

_id = 0
"""int
The component's unique id.
"""


def create_action(action, component, reducer_name):
    """Create a redux-compatible action.

    Given an action, return a lambda function that connects this component with the `Root` component and
    the action reducer so that every time an action resolves, this components receives the results as props.

    Args:
        action ((tuple) -> dict): Whatever's returned by this action will be reduced by its respective reducer.
        component (Component): The component that will receive the action's result as props.
        reducer_name (str): The name of the reducer that will process this action.

    Returns:
        FunctionType: The lambda function that links reducers to this component

    """
    return lambda *args: connect_action(action, component, reducer_name, *args)


def connect_reducer(component, actions, props):
    """Link actions with reducers.

    Given a list of raw actions (functions), first make its actions redux-compatible and then connect them with the
    reducers responsible of handling those specific actions. The component's regular props are combined with
    redux props at the end of this method.

    Note:
        See `react.redux.index` to understand `set_reducers_to_default`

    Args:
        component (Component): The component to connect the actions with.
        actions (dict of str: (dict of str: ((tuple) -> dict))): Contains a dict for each reducer, which in turn contains that
            reducer's actions.
        props (dict): The original properties passed to this component by its parent.

    """
    combined_props = props.copy()

    for reducer_name, reducer_actions in actions.items():
        reducer_props = {}

        for action_name, action in reducer_actions.items():
            reducer_props[action_name] = create_action(action, component, reducer_name)

        combined_props[reducer_name] = NamedTuple(reducer_props, reducer_name + 'props')

    component.props = NamedTuple(combined_props, 'props')
    set_reducers_to_default(component, actions.keys())

    return component.props


def get_component_id():
    """Index components.

    This function is called every time a new component is created to bind it with a unique id to distinguish it
    from other components and to easily identify it again.

    Returns:
        int: A unique id for a new component.

    """
    global _id
    curr_id = _id
    _id += 1

    return curr_id


def wrapper(method):
    """Executes before calling methods of the Component class.

    This is where most of the `React` behavior setup takes place behind the scenes.

    Args:
        method (() -> Any): The method currently being wrapped

    Returns:
        Whatever the original wrapped method would have returned

    """
    @wraps(method)
    def wrapped(*args, **kwargs):
        """The actual wrapper function.

        After evaluating certain conditions, this method takes care of any preparation or
        operation needed by a general purpose React Component. When the `render` method is called on a
        specific `Component`, certain operations happen in the following order, where steps 1-2 are
        pre-rendering operations and steps 4- involve post-rendering operations:

            1) Call `component_will_mount` on the component iff the component is hidden
            2) If the component has a parent `Component` i.e. if the component is not Root, acknowledge the
                rendering of this component by referencing it in its parent's `renders` list. This
                step together with `step 3` is key to hiding non-rendered components automatically.
            3) Actually render the component i.e call its `render` method
            4) For clarity, let's name the component's `widget_renders`, W, and `renders`, R. First of all,
                the component's entire list of hidden and rendered `widgets` and `children` get temporarily cloned into
                the variables `hidden_wiggets` and `hidden_children` respectively. So if we name the former HW and the
                latter HC, then the set HW \ W represents the total number of children widgets that will be
                rendered, and analogously, R \ HC represents the set of all children that need to be
                rendered. Therefore, this step is responsible for making this distinction and reducing HW to HW \ W
                and HC to R \ HC, thus preparing components and widgets to be rendered or hidden.
            5) Hide all widgets in HW and components in HC.

        On the other hand, if the `component_will_receive_props` method is called on a specific `Component`,
        this wrapper allows the user to explicitly decide exactly when the component's parent should pass it
        its respective props by calling `ready_props` from within the `component_will_receive_props` overridden method
        (if the user does not call `ready_props`, this happens automatically after calling
        `component_will_receive_props`).

        Args:
            *args: Variable length argument list for the method being wrapped, where `args[0]` is always
                `self`.
            **kwargs: Arbitrary keyword arguments

        Returns:
            FunctionType: The wrapped method or the original method depending on the specific behavior
            desired.

        """
        self = args[0]
        func_name = method.__name__

        if config['log'] == 2:
            print func_name, args, kwargs

        if func_name == 'render':  #: wrap `render` method
            if not hasattr(self, 'never_rendered'):
                print self

            if self.hidden or (hasattr(self, 'never_rendered') and self.never_rendered):  #: step 1
                if hasattr(self, 'never_rendered') and self.never_rendered:
                    self.never_rendered = False

                self.component_will_mount()

            self.hidden = False

            self.renders.clear()  #: step 2
            self.widget_renders.clear()

            if self.parent is not None:  #: if not Root component
                self.parent.renders.insert(self)

            res = method(*args, **kwargs)  #: step 3: calling `render`

            hidden_widgets = self.widgets.__copy__()  #: step 4
            hidden_components = self.children.__copy__()

            for child in self.widget_renders:
                hidden_widgets.remove(child)

            for child in self.renders:
                hidden_components.remove(child)

            for hidden_child in hidden_widgets:  #: step 5
                if hidden_child.id != 0:
                    hidden_child.pack_forget()
                    hidden_child.place_forget()
                    hidden_child.grid_forget()

            for hidden_child in hidden_components:
                if not hidden_child.hidden:
                    hidden_child.forget()

            return res

        if func_name == 'component_will_receive_props':
            self.props_pending = True
            res = method(*args, **kwargs)

            if self.props_pending:
                self.ready_props(args[1])

            return res

        return method(*args, **kwargs)

    return wrapped


class MetaClass(type):
    """The meta class that wraps React Components.

    """
    def __new__(mcs, class_name, bases, class_dict):
        """ Connects Components with the `wrapper` method.

        Args:
            class_name (str): The name of the class to be wrapped i.e. 'Component'.
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
        return type.__new__(mcs, class_name, bases, new_class_dict)


class Component(MetaClass('Component', (object,), {})):
    """React Component.

    The usual implementation of Facebook's React state, props, and redux data flow. Although there are some
    limitations to this implementation (see this module's `Todo` section), the basic behavior works well.

    In order to extend this class, a component, say component `A`, must make the call
    `super(A, self).__init__(*args, **kwargs)` to initialize this class (see `Example`).

    Note:
        Just like in Facebook's React, the state should only be set once at the beginning of the component's
        `__init__` method right after the call to `super` but after the optional call to `import_actions`
        and should only be updated with a call to `self.set_state`.

    Example:
    ::
        import react.index as react
        from react.component import Component
        from reducers.index import root_reducer

        def map_state_to_props(state):
            return dict(redux_prop1=state.reducer_name.prop1, redux_prop2=state.reducer_name.prop2)

        class ChildComponent(Component):
            def __init__(self, parent, **props):
                super(childComponent, self).__init__(parent, **props)
                self.state = dict(self, state_var1=state_var1, state_var2=state_var1)
                ...
                self.set_state(dict(width=500, height=618))

        class A(Component):
            def __init__(self, parent, **props):
                import_actions = dict(reducer_name=dict(action1=action1, action2=action2))
                super(A, self).__init__(parent, import_actions=import_actions, map_state_to_props=map_state_to_props,
                                        root_reducer=root_reducer, **props)

                state_var1 = 10

                self.state = dict(self, state_var1=state_var1, state_var2="state_var2")

                self.width = 100
                self.height = 200

                self.frame = react.Frame(self, bg='black', frame=self.parent_frame, width=self.width,
                                         height=self.height)

                self.childComponent = ChildComponent(self, frame=self.frame, width=50, height=50, x=10, y=10,
                                                     prop1=prop1, prop2=prop2)
                ...
                new_val_1 = self.state.state_var1 + 12
                self.set_state(dict(state_var1=new_val_1))

    Attributes:
        id (int): The component's unique id.
        parent_frame (react.widget_wrappers.Frame): The default react frame widget that will be used as this component's
            default parent frame for Tkinter purposes.
        children (react.data_structures.doubly_linked_list.DoublyLinkedList of Component): The React components
            contained in the current component.
        widgets (react.data_structures.doubly_linked_list.DoublyLinkedList of Tkinter.Widget): The React-wrapped Tkinter
            widgets contained in the current component.
        renders (react.data_structures.doubly_linked_list.DoublyLinkedList of Component): A subset of `self.children`
            that contains the components to be rendered.
        widget_renders (react.data_structures.doubly_linked_list.DoublyLinkedList of Tkinter.Widget): A subset of
            `self.widgets` that contains the widgets to be rendered.
        state (dict): A mapping of the component's state keys and values
        width (float): The component's width (rounded to the closest int). None means default width.
        height (float): The component's height (rounded to the closest int). None means default height.
        x (float): The component's horizontal offset. Default is 0.
        y (float): The component's vertical offset. Default is 0.
        props (tuple): This component's props (both by reducers and by the parent)
        map_state_to_props ((tuple) -> dict): Indicates how to map the responses generated by the reducers to props for
            this given component (to self.props).

    """
    def __init__(self, parent, frame, width=None, height=None, x=None, y=None, map_state_to_props=None,
                 actions=None, root_reducer=None, **props):
        """`Component` __init__ method.

        Args:
            parent (Component, optional): `self.parent`
            frame (react.widget_wrappers.Frame): `self.parent_frame`
            width (float, optional): `self.width`. Default is None, which means default width.
            height (float, optional): `self.height`. Default is None, which means default height.
            x (float, optional): `self.x`. Default is None, which means 0.
            y (float, optional): `self.y` Default is None, which means 0.
            map_state_to_props ((tuple) -> dict, optional): `self.map_state_to_props`. Default is None, which implies no
                actions will be reduced.
            actions (dict of str: (dict of str: ((tuple) -> dict)), optional): Contains a dict for each reducer, which
                in turn contains that reducer's actions. Default is None, which implies no actions will be imported.
            root_reducer (:obj:`Reducer`, optional):  `self.root_reducer`. Default is None, which means no root reducer.
            **props: The properties that this component's parent will continually pass to `self.props`.

        """
        self.id = get_component_id()
        self.parent_frame = frame
        self.children = DoublyLinkedList()
        self.widgets = DoublyLinkedList()
        self.renders = DoublyLinkedList()
        self.widget_renders = DoublyLinkedList()
        self.width = None if width is None else int(np.round(width))
        self.height = None if height is None else int(np.round(height))
        self.x = None if x is None else int(np.round(x))
        self.y = None if y is None else int(np.round(y))

        self.__parent = parent
        self.parent = self.__parent
        self.__state = None
        self.state = self.__state
        self.__root_reducer = root_reducer
        self.root_reducer = self.__root_reducer

        self.map_state_to_props = map_state_to_props
        self.props = connect_reducer(self, actions, props) if actions is not None else NamedTuple(props, 'props')

        self.hidden = False
        self.never_rendered = True
        self.props_pending = False

    def __eq__(self, other):
        """Check for Component equality.

        Args:
            other (Component): The other component to compare this component with.

        Returns:
            bool: True if the other component is the same component, False otherwise.

        """
        return isinstance(other, Component) and self.id == other.id

    @property
    def parent(self):
        """Component: The component that contains this component"""
        return self.__parent

    @parent.setter
    def parent(self, value):
        self.__parent = value

        if value is not None:  #: add this component as a child
            value.add_child(self)

    @property
    def state(self):
        """dict: A mapping of the component's state keys and values"""
        return self.__state

    @state.setter
    def state(self, value):
        self.__state = value if value is None else NamedTuple(value, 'state')

    @property
    def root_reducer(self):
        """react.redux.reducer.Reducer: The reducer that will connect actions with the component's props."""
        return self.__root_reducer

    @root_reducer.setter
    def root_reducer(self, value):
        self.__root_reducer = value

        if value is not None:
            set_root_reducer(value)  #: connect it with redux

    def add_child(self, child):
        """Add a child component to be contained in this component.

        Args:
            child (Component): This component will be added as a child.

        """
        self.children.insert(child)

    def ready_props(self, props):
        """Finalize passing props to child.

        After this component's `component_will_receive_props` gets called, the user can use this method
        indicate that the processing of the new props has been finished and to set the value of the actual
        props variables.

        Args:
            props (react.data_structures.named_tuple.NamedTuple): Component's new props.

        """
        self.props = self.props._replace(**(props._asdict()))
        self.props_pending = False

    def update_props(self, state):
        """Update old props to new ones.

        This method is responsible for passing this component's props all the way down the chain and calling
        the `component_will_receive_props` of all the components affected. These operations happen in the
        following order in a recursive manner up down to the last child with at least one props change:

            1) Track prop changes and disregard repeated props.
            2) Merge any new props with the old props.
            3) Given at least one updated prop, call the component's `component_will_receive_props` method
            4) Pass the new props down to all the component's children
            5) Given at least one change, render the component once more.

        Args:
            state (dict): Updated state of props.

        """
        props_dict = self.props._asdict()
        new_props = {}
        existing_props = {}

        for prop_name, prop in state.items():  #: step 1
            if prop_name not in props_dict.keys():
                new_props[prop_name] = prop
            else:
                existing_props[prop_name] = prop

        if len(new_props) > 0:  #: step 2
            out_props = new_props.copy()

            for key, val in props_dict.items():
                out_props[key] = val

            self.props = NamedTuple(out_props, 'props')

        if len(existing_props) > 0:  #: step 3
            self.component_will_receive_props(NamedTuple(existing_props, 'NewProps'))

        self.pass_props(state)  #: step 4

        if len(existing_props) > 0:  #: step 5
            if self.never_rendered:
                self.never_rendered = False
                self.component_will_mount()

            self.render()

    def pass_props(self, state):
        """Recursively pass props down the chain.

        The method `update_props` finalizes the data flow from the component's parent to the component itself,
        but in `step 4` `update_props` call `pass_props` to recursively do the same for all descendants of
        the parent. The process finally stops when the new props first do not concern a component, say component A.
        We can now assume that all descendants of A will not be interested in the new props either because
        the chain is broken, and there is no connection left to those props.

        Args:
            state (dict): Updated state of props.

        """
        for child in self.renders:
            assert isinstance(child, Component)
            props = {}
            old_props = child.props._asdict()

            for key, val in state.items():  #: check for only NEW props
                if key in old_props.keys():
                    props[key] = val

            if len(props) > 0:  #: otherwise, terminate the recursion
                child.component_will_receive_props(NamedTuple(props, 'props'))

                if not child.children.is_empty():
                    child.pass_props(props)

    def set_state(self, state):
        """Update component's state.

        This is the only way a component's state should be modified (as exemplified by this class's
        description). After the component's state is set to the updated version, then a call to this
        component's `pass_props` method is made to pass the state down as props down the chain.

        Args:
            state (dict): New component state.

        """
        self.state = state if self.state is None else self.state._replace(**state)._asdict()
        self.pass_props(state)
        self.render()

    def render(self):
        """Display the component's new state.

        This method needs to be overridden by another class that extends this class, otherwise
        this method does nothing.

        """
        pass

    def forget(self):
        """Hide all the widgets in this component's.

        Loops over the `DoublyLinkedList` of widgets in this components and hides them according
        to Tkinter's spec.

        """
        self.hidden = True

        for widget in self.widgets:
            widget.pack_forget()
            widget.place_forget()
            widget.grid_forget()

    def component_will_receive_props(self, props):
        """The component's props are about to be updated.

        This method gets called whenever reducers or parent components pass props down to this component,
        and should be overridden by another class that extends this class to handle the event as desired.

        Args:
            props (react.data_structures.named_tuple.NamedTuple): The new props that haven't been updated yet.

        """
        pass

    def component_will_mount(self):
        """The component will be rendered having been previously hidden.

        This method gets called whenever a hidden component is about to get rendered for the first time after
        being hidden, and should be overridden by another class that extends this class to handle the event
        as desired.

        """
        pass
