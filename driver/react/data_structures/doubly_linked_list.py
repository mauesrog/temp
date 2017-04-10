"""Doubly-linked list class definition.

Defines a general purpose doubly-linked list data structure with a nested class to define the nodes of the list.

.. _React Library:
    https://github.com/hivebattery/gui/blob/master/driver/react/data_structures/doubly_linked_list.py

"""


class DoublyLinkedList(object):
    """General purpose doubly-linked list.

    Behaves as a FIFO.

    Attributes:
        __sentinel (DoublyLinkedList.DoublyLinkedListNode): The list's sentinel with a dummy value.
        __auto_pop (bool): Whether nodes should be removed after iterating through them.
        __size (int): The number of elements currently in the list.

    """
    class DoublyLinkedListNode(object):
        """General purpose doubly-linked list node.

        """
        def __init__(self, val):
            """Doubly-linked List Node constructor.

            Initializes the node to the default i.e. a node that's not in any list. The object to be stored
            in the node is also specified here.

            Args:
                val: The object to be stored in the node.

            """
            self.__next = self
            self.__prev = self
            self.__value = val

        def __str__(self):
            """Stringify node.

            Provides a more representative string representation of this node.

            Returns:
                str: The string representation of the object stored in this node.

            """
            return str(self.value)

        @property
        def next(self):
            """DoublyLinkedList.DoublyLinkedListNode: The node inserted to the list right before this one.
            """
            return self.__next

        @next.setter
        def next(self, value):
            self.__next = value

        @property
        def prev(self):
            """DoublyLinkedList.DoublyLinkedListNode: The node inserted to the list right after this one.
            """
            return self.__prev

        @prev.setter
        def prev(self, value):
            self.__prev = value

        @property
        def value(self):
            """The object stored in the node.
            """
            return self.__value

        @value.setter
        def value(self, value):
            self.__value = value

        def splice_right(self, node):
            """Adds a new node to the right of the sentinel.

            Args:
               node (DoublyLinkedList.DoublyLinkedListNode): The node to be spliced in.

            """
            node.next = self.next
            node.prev = self

            self.next = node
            node.next.prev = node

        def splice_out(self):
            """Removes a node from the list.

            """
            self.prev.next = self.next
            self.next.prev = self.prev

    def __init__(self, auto_pop=False):
        """Doubly-linked List constructor.

        Initializes the list to the default i.e. an empty list with a sentinel.

        Args:
            auto_pop (bool): See `self.auto_pop`.

        """
        self.__sentinel = self.DoublyLinkedListNode(None)
        self.__auto_pop = auto_pop

        self.__size = 0

    def __len__(self):
        """`self.__size` getter.

        Returns:
            int: The number of elements in the list.

        """
        return self.__size

    def __str__(self):
        """Stringify the entire list.

        Joins the string representation of each nodes with a comma.

        Returns:
            str: The string representation of the list.

        """
        return ", ".join([str(node) for node in self])

    def __iter__(self):
        """List iterator.

        If auto pop is active, all elements are removed after being yielded.

        Yields:
            The object in the next node.

        """
        node = self.__sentinel.prev

        while not self.__is_sentinel(node):
            val = node.value
            prev_node = node.prev

            if self.__auto_pop:
                self.__size -= 1
                node.splice_out()

            node = prev_node

            yield val

    def __copy__(self):
        """Clone this list.

        Returns:
            DoublyLinkedList: A deep copy of the list.

        """
        copy = DoublyLinkedList()

        for node in self:
            copy.insert(node)

        return copy

    def insert(self, val):
        """Insert a new object to the list.

        A new node is created to hold this object.

        Args:
            val: The object to be inserted.

        """
        node = self.DoublyLinkedListNode(val)
        self.__sentinel.splice_right(node)
        self.__size += 1

    def remove(self, val):
        """Remove the node that contains this specific object.

        Given that this method relies on the object's implementation of `__eq__` and that there is no indexing,
        the time complexity to remove an object is O(n).

        Args:
            val: The object to be removed.

        Returns:
            bool: True if the object was matched and removed, False otherwise.

        """
        node = self.__sentinel.prev

        while not self.__is_sentinel(node):
            if node.value == val:
                node.splice_out()
                return True

            node = node.prev

        return False

    def is_empty(self):
        """Check if the list is empty.

        Returns:
            bool: True if the list is empty, False otherwise.

        """
        return self.__size == 0

    def pop(self):
        """Return and remove the element that was inserted first to the list.

        Returns:
            The object in the node removed.

        """
        if not self.is_empty():
            val = self.__sentinel.prev.value
            self.__sentinel.prev.splice_out()
            self.__size -= 1
        else:
            val = None

        return val

    def clear(self):
        """Reset the list to its default, empty state.

        """
        self.__sentinel = self.DoublyLinkedListNode(None)
        self.__size = 0

    def toggle_auto_pop(self):
        """Activate or deactivate the auto pop feature.

        Note:
            See `self.__auto_pop`.

        """
        self.__auto_pop = not self.__auto_pop

    def get_last(self):
        """Return the element that was inserted first to the list, without removing it.

        Returns:
            The object in the node that was first inserted to the list.

        """
        return self.__sentinel.prev

    @staticmethod
    def __is_sentinel(node):
        """Checks if the node is the sentinel.

        Args:
            node (DoublyLinkedList.DoublyLinkedListNode): The node that will be subjected to the test.

        Returns:
            bool: True if the node is the sentinel, False otherwise.

        """
        return node.value is None
