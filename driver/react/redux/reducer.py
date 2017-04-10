"""Redux Reducer definition.

Contains the `Reducer` class which is added to the root reducer.

.. _React Library:
    https://github.com/hivebattery/gui/blob/master/driver/react/redux/reducer.py

"""

from __future__ import absolute_import
from ..data_structures.named_tuple import NamedTuple


class Reducer(object):
    """Redux Reducer.

    This class should be extended by any user-created reducers. The only special aspect of this class
    is its method `reduce_action` because it needs to be overridden so that the action gets actually
    processed and not just ignored.

    Attributes:
        state (react.data_structures.named_tuple.NamedTuple): Initially the default state for this reducer, but it
            evolves with the reducer's updates.

    """
    def __init__(self, default_val):
        self.state = NamedTuple(default_val, 'ReducerState')

    def reduce_action(self, action):
        """Process action and reduce it to a dict.

        This method should be overridden to inspect the action and return whatever resolves from the action's results.

        Args:
            action (react.data_structures.named_tuple.NamedTuple): Contains the results of the action. It needs to
                contain a type string property to identify what kind of action is being reduced.

        """
        pass
