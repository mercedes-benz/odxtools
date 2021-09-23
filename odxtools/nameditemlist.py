# SPDX-License-Identifier: MIT
# Copyright (c) 2021 MBition GmbH

from typing import List, Union

class NamedItemList:
    """A list that provides direct access to its items as named attributes.

    This is a hybrid between a list and a user-defined object: One can
    iterate over all items of the list as usual, but items can also be
    accessed via `named_list.itemname`, where the 'itemname' is
    specified via a item -> string mapping function that is passed to
    the constructor.

    If an item name is not unique, `_<num>` will be appended to
    avoid naming collisions. The user is responsible that the strings
    returned by the item-to-name function are valid identifiers in python.
    """
    def __init__(self, item_to_name_fn, input_list = None):
        self._item_to_name_fn = item_to_name_fn
        self._list = []
        if input_list is not None:
            for item in input_list:
                self.append(item)

    def append(self, item):
        """
        Append a new item to the list and make it accessible as a
        member attribute.

        \return The name under which item is accessible
        """
        self._list.append(item)

        item_name = self._item_to_name_fn(item)
        i = 1
        tmp = item_name
        while True:
            if tmp not in self.__dict__:
                self.__dict__[tmp] = item
                return tmp

            i += 1
            tmp = f"{item_name}_{i}"

    def __len__(self):
        return len(self._list)

    def __getitem__(self, key: Union[int, str]):
        if isinstance(key, int):
            return self._list[key]
        else:
            return self.__dict__.get(key)

    def __str__(self):
        return f"[{', '.join([self._item_to_name_fn(s) for s in self._list])}]"

    def __repr__(self):
        return self.__str__()
