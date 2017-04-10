"""Redux. Main module.

Connects `React` components with action so that whenever an action resolves, the components receive the results
as props.

Todo:
    * Test a root reducer with more than one reducer.

.. _React Library:
    https://github.com/hivebattery/gui/blob/master/driver/react/redux/index.py

"""
from __future__ import absolute_import

from ..data_structures.named_tuple import NamedTuple
from ..index import set_timeout

_root_reducer = None
"""dict of react.redux.reducer.Reducer

The main reducer that will store references to all specific reducers.
"""


def combine_reducers(**reducers):
    """Build a root reducer.

    Create an object such that each attribute represents a specific reducer with its respective key.

    Args:
        **reducers (dict of react.redux.reducer.Reducer): An arbitrary number of reducers.

    Returns:
        react.data_structures.named_tuple.NamedTuple: The root reducer with all reducers set as attributes.

    """
    return NamedTuple(reducers, 'RootReducer')


def set_root_reducer(reducer):
    """`_root_reducer` setter.

    Args:
        reducer (react.data_structures.named_tuple.NamedTuple of react.redux.reducer.Reducer):
            The root reducer with all reducers set as attributes.

    """
    global _root_reducer
    _root_reducer = reducer


def process_response(action, component, reducer_name, *args):
    """Reduce action and pass results as props.

    Args:
        action ((tuple) -> dict): Whatever's returned by this action will be reduced by its respective reducer.
        component (react.component.Component): The component that will receive the action's result as props.
        reducer_name (str): The name of the reducer that will process this action.
        *args: The arguments to be passed to the action.

    """
    k = action(*args)

    if k is not None:
        reducer_dict = {}

        res = NamedTuple(k, 'NewAction')
        new_state = _root_reducer._asdict()[reducer_name].reduce_action(res)

        reducer_dict[reducer_name] = new_state

        data = NamedTuple(reducer_dict, reducer_name.upper() + 'NewState')
        component.update_props(component.map_state_to_props(data))


def connect_action(action, component, reducer_name, *args):
    """Trigger the action with Tkinter's background event handler.

    Args:
        action ((tuple) -> dict): Whatever's returned by this action will be reduced by its respective reducer.
        component (react.component.Component): The component that will receive the action's result as props.
        reducer_name (str): The name of the reducer that will process this action.
        *args: The arguments to be passed to the action.

    """
    set_timeout(100, lambda: process_response(action, component, reducer_name, *args))


def set_reducers_to_default(component, reducer_names):
    """Default reducer states.

    Set all reducers to the default state and pass the results as props.

    Args:
        component (react.component.Component): The component that will receive the action's result as props.
        reducer_names (list of str): The name of the reducer that will process this action.

    """
    new_state_dict = {}
    root_reducer_dict = _root_reducer._asdict()

    for reducer_name in reducer_names:
        new_state_dict[reducer_name] = root_reducer_dict[reducer_name].state

    data = NamedTuple(new_state_dict, 'NewState')
    component.update_props(component.map_state_to_props(data))