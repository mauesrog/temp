"""Root Reducer Definition.

Up to this point, the USB reducer is the only one implemented.

"""
from __future__ import absolute_import

from react.redux.index import combine_reducers
from .usb_reducer import USBReducer

root_reducer = combine_reducers(usb=USBReducer())
"""react.data_structures.named_tuple.NamedTuple: Contains the USB reducer as its only attributes.
"""
