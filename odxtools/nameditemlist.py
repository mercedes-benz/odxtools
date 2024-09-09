# SPDX-License-Identifier: MIT
import abc
import typing
from copy import deepcopy
from keyword import iskeyword
from typing import (Any, Collection, Dict, Iterable, List, Optional, SupportsIndex, Tuple, TypeVar,
                    Union, cast, overload, runtime_checkable)

from .exceptions import odxraise


@runtime_checkable
class OdxNamed(typing.Protocol):

    @property
    def short_name(self) -> str:
        ...


T = TypeVar("T")
TNamed = TypeVar("TNamed", bound=OdxNamed)


class ItemAttributeList(List[T]):
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

    def __init__(self, input_list: Optional[Iterable[T]] = None) -> None:
        self._item_dict: Dict[str, T] = {}

        if input_list is not None:
            for item in input_list:
                self.append(item)

    @abc.abstractmethod
    def _get_item_key(self, item: T) -> str:
        pass

    def append(self, item: T) -> None:
        """
        Append a new item to the list and make it accessible as a
        member attribute.

        \return The name under which item is accessible
        """
        self._add_attribute_item(item)

        super().append(item)

    def _add_attribute_item(self, item: T) -> None:
        item_name = self._get_item_key(item)

        # eliminate conflicts between the name of the new item and
        # existing attributes of the ItemAttributeList object
        i = 1
        tmp = item_name
        while True:
            if not hasattr(self, tmp):
                break

            i += 1
            if item_name.endswith("_"):
                # if the item name already ends with an underscore,
                # there's no need to add a second one...
                tmp = f"{item_name}{i}"
            else:
                tmp = f"{item_name}_{i}"

        item_name = tmp

        self._item_dict[item_name] = item

    def insert(self, index: SupportsIndex, obj: T) -> None:
        self._add_attribute_item(obj)

        list.insert(self, index, obj)

    def remove(self, obj: T) -> None:
        list.remove(self, obj)

        keys = [k for (k, v) in self._item_dict.items() if v == obj]
        for key in keys:
            del self._item_dict[key]

    def pop(self, index: SupportsIndex = -1) -> T:
        result = list.pop(self, index)
        keys = [k for (k, v) in self._item_dict.items() if v == result]
        for key in keys:
            del self._item_dict[key]
        return result

    def extend(self, items: Iterable[T]) -> None:
        for item in items:
            self.append(item)

    def clear(self) -> None:
        super().clear()

        self._item_dict = {}

    def copy(self) -> "ItemAttributeList[T]":
        result = self.__class__()
        for item in self:
            list.append(result, item)
        result._item_dict = self._item_dict.copy()
        return result

    def keys(self) -> Collection[str]:
        return self._item_dict.keys()

    def values(self) -> Collection[T]:
        return self._item_dict.values()

    def items(self) -> Collection[Tuple[str, T]]:
        return self._item_dict.items()

    def __dir__(self) -> Dict[str, Any]:
        result = dict(self.__dict__)
        result.update(self._item_dict)
        return result

    @overload
    def __getitem__(self, key: SupportsIndex) -> T:
        ...

    @overload
    def __getitem__(self, key: str) -> T:
        ...

    @overload
    def __getitem__(self, key: slice) -> List[T]:
        ...

    def __getitem__(self, key: Union[SupportsIndex, str, slice]) -> Union[T, List[T]]:
        if isinstance(key, (SupportsIndex, slice)):
            return super().__getitem__(key)
        else:
            return self._item_dict[key]

    def __getattr__(self, key: str) -> T:
        if key not in self._item_dict:
            raise AttributeError(f"ItemAttributeList does not contain an item named '{key}'")

        return self._item_dict[key]

    def get(self, key: Union[int, str], default: Optional[T] = None) -> Optional[T]:
        if isinstance(key, int):
            if 0 <= key and key < len(self):
                return super().__getitem__(key)
            return default
        else:
            return cast(Optional[T], self._item_dict.get(key, default))

    def __eq__(self, other: object) -> bool:
        """
        Item lists are equal if the underlying lists are equal.
        """
        if not isinstance(other, type(self)) or not isinstance(self, type(other)):
            return False
        else:
            return self._item_dict == other._item_dict

    def __str__(self) -> str:
        return f"[{', '.join( [self._get_item_key(x) for x in self])}]"

    def __repr__(self) -> str:
        return f"{type(self).__name__}([{', '.join([repr(x) for x in self])}])"

    def __copy__(self) -> Any:
        return self.__class__(list(self))

    def __deepcopy__(self, memo: Dict[int, Any]) -> Any:
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result
        result._item_dict = {}
        for x in self:
            result.append(deepcopy(x, memo))

        return result


class NamedItemList(ItemAttributeList[T]):

    def _get_item_key(self, item: T) -> str:
        """Transform an object's `short_name` attribute into a valid
        python identifier

        Although short names are almost identical to valid python
        identifiers, their first character is allowed to be a number or
        they may be python keywords. This method prepends an underscore to
        such short names.

        """
        if not isinstance(item, OdxNamed):
            odxraise()
        sn = item.short_name
        if not isinstance(sn, str):
            odxraise()

        # make sure that the name of the item in question is not a python
        # keyword (this would lead to syntax errors) and that does not
        # start with a digit
        if sn[0].isdigit() or iskeyword(sn):
            return f"_{sn}"

        return sn
