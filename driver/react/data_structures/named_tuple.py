"""NamedTuple class definition.

Wraps a `collection.namedtuple` object for the sake of documentation.

Note:
    See Python's documentation for `collection.namedtuple` for more information.

Example:
::
    data_dict = dict(prop1='hello', prop2='this is an example.')
    named_tuple = NamedTuple(data_dict, 'Example')

    print named_tuple.prop1, named_tuple.prop2
    #: prints 'Hello this is an example.'

.. _React Library:
    https://github.com/hivebattery/gui/blob/master/driver/react/data_structures/named_tuple.py

"""
from __future__ import absolute_import
from collections import namedtuple


class NamedTuple(object):
    """NamedTuple.

    Given any name, transforms a dict into an instance of `collections.namedtuple` so that the items of the dict
    can be accessed as attributes with dot notation.

    """
    def __init__(self, data, name):
        """NamedTuple constructor.

        Args:
            data (dict): The dictionary with the keys and values that will be turned into attribute keys and attributes,
                respectively.
            name (str): Defines the `collections.namedtuple` object name.

        """
        self.__named_tuple = namedtuple(name, ' '.join(data.keys()))(**data)

    @property
    def namedtuple(self):
        """collections.namedtuple: The actual namedtuple object"""
        return self.__named_tuple

    def __getattr__(self, item):
        """Custom NamedTuple attribute retrieval.

        Relieves all attribute retrieval to the actual `collections.namedtuple` object, except for '__named_tuple',
        which provides direct access to the namedtuple object.

        Args:
            item (str): The name of the desired attribute.

        Returns:
            The `collections.namedtuple` object attribute if `item` is not '__named_tuple', the namedtuple object
            otherwise.

        """
        if item == '__named_tuple' or item == 'namedtuple':
            return getattr(self, item)

        return getattr(self.__named_tuple, item)
