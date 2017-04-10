"""Queue class definition.

.. _src-common-queue:
    https://github.com/hivebattery/gui/blob/master/driver/src/common/data_structures/queue.py

"""


class Queue:
    """Queue.

    A FIFO that recognizes whether an object has already been inserted to the queue and calls a callback each time
    a new item is successfully inserted.

    Attributes:
        q (dict): The queue.

    """
    def __init__(self, c):
        """Queue constructor.

        Args:
            c (() -> None): The callback to call each time a new item is inserted.

        """
        self.__callback = c
        self.q = {}

    def __iter__(self):
        """Queue iterator.

        Go through all the items in the queue and yield each value.

        Yields:
            The values stored in the queue.

        """
        for val in self.q.values():
            yield val

    @property
    def callback(self):
        """(() -> None): The callback to call each time a new item is inserted.
        """
        return self.__callback

    @callback.setter
    def callback(self, value):
        self.__callback = value

    def push(self, obj):
        """Insert new item into the queue.

        Only new items are inserted.

        Args:
            obj: The item to be inserted.

        """
        if str(obj) not in self.q.keys():
            if len(self.q) > 0:
                [key] = self.q.keys()
                del self.q[key]

            self.q[str(obj)] = obj
            self.callback()

    def pop(self):
        """Remove an item from the queue.

        Returns:
            The first value in the FIFO.

        """
        [key] = self.q.keys()
        [val] = self.q.values()

        del self.q[key]
        return val
