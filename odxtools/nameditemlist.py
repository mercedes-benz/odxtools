# SPDX-License-Identifier: MIT
import abc
from collections import OrderedDict
from keyword import iskeyword
from typing import (Any, Callable, Collection, Dict, Generic, Iterable, Iterator, List, Optional,
                    Protocol, Tuple, TypeVar, Union, cast, overload, runtime_checkable)

from .exceptions import odxraise


@runtime_checkable
class OdxNamed(Protocol):

    @property
    def short_name(self) -> str:
        pass


T = TypeVar("T")
TNamed = TypeVar("TNamed", bound=OdxNamed)


class ItemAttributeList(Generic[T]):
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
        self._item_dict: OrderedDict[str, T] = OrderedDict()
        self._item_list: List[T] = []

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
        self._item_list.append(item)

    def sort(self, key: Optional[Callable[[T], str]] = None, reverse: bool = False) -> None:
        if key is None:
            self._item_dict = OrderedDict(
                sorted(self._item_dict.items(), key=lambda x: x[0], reverse=reverse))
        else:
            key_fn = cast(Callable[[T], str], key)
            self._item_dict = OrderedDict(
                sorted(self._item_dict.items(), key=lambda x: key_fn(x[1]), reverse=reverse))

        self._item_list = list(self._item_dict.values())

    def keys(self) -> Collection[str]:
        return self._item_dict.keys()

    def values(self) -> Collection[T]:
        return self._item_list

    def items(self) -> Collection[Tuple[str, T]]:
        return self._item_dict.items()

    def __contains__(self, x: T) -> bool:
        return x in self._item_list

    def __len__(self) -> int:
        return len(self._item_list)

    def __dir__(self) -> Dict[str, Any]:
        result = dict(self.__dict__)
        result.update(self._item_dict)
        return result

    @overload
    def __getitem__(self, key: int) -> T:
        ...

    @overload
    def __getitem__(self, key: str) -> T:
        ...

    @overload
    def __getitem__(self, key: slice) -> List[T]:
        ...

    def __getitem__(self, key: Union[int, str, slice]) -> Union[T, List[T]]:
        if isinstance(key, int):
            return self._item_list[key]
        elif isinstance(key, slice):
            return self._item_list[key]
        else:
            return self._item_dict[key]

    def __getattr__(self, key: str) -> T:
        if key not in self._item_dict:
            raise AttributeError(f"ItemAttributeList does not contain an item named '{key}'")

        return self._item_dict[key]

    def get(self, key: Union[int, str], default: Optional[T] = None) -> Optional[T]:
        if isinstance(key, int):
            if abs(key) < -len(self._item_dict) or key >= len(self._item_dict):
                return default

            return self._item_list[key]
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

    def __iter__(self) -> Iterator[T]:
        return iter(self._item_list)

    def __str__(self) -> str:
        return f"[{', '.join(self._item_dict.keys())}]"

    def __repr__(self) -> str:
        return self.__str__()


def short_name_as_key(obj: OdxNamed) -> str:
    """Transform an object's `short_name` attribute into a valid
    python identifier

    Although short names are almost identical to valid python
    identifiers, their first character is allowed to be a number or
    they may be python keywords. This method prepends an underscore to
    such short names.

    """
    if not isinstance(obj, OdxNamed):
        odxraise()
    sn = obj.short_name
    if not isinstance(sn, str):
        odxraise()

    # make sure that the name of the item in question is not a python
    # keyword (this would lead to syntax errors) and that does not
    # start with a digit
    if sn[0].isdigit() or iskeyword(sn):
        return f"_{sn}"

    return sn


class NamedItemList(Generic[TNamed], ItemAttributeList[TNamed]):

    def _get_item_key(self, obj: OdxNamed) -> str:
        return short_name_as_key(obj)
