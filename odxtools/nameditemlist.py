# SPDX-License-Identifier: MIT
import abc
from keyword import iskeyword
from typing import (Callable, Collection, Generic, Iterable, List, Optional, Protocol, Tuple,
                    TypeVar, Union, cast, overload, runtime_checkable)

from .exceptions import odxassert, odxraise


@runtime_checkable
class OdxNamed(Protocol):

    @property
    def short_name(self) -> str:
        pass


T = TypeVar("T")
TNamed = TypeVar("TNamed", bound=OdxNamed)


class ItemList(Generic[T]):
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
        self._names: List[str] = []
        self._values: List[T] = []

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

        # eliminate conflicts between the item name and existing
        # attributes of the NamedItemList object
        i = 1
        tmp = item_name
        while True:
            # using dir() for checking if there is a name conflict
            # might be slow, but NamedItemList is not meant for
            # ginormous lists...
            if tmp not in dir(self):
                break

            i += 1
            if item_name.endswith("_"):
                tmp = f"{item_name}{i}"
            else:
                tmp = f"{item_name}_{i}"
        item_name = tmp

        self.__dict__[item_name] = item
        self._names.append(item_name)
        self._values.append(item)

    def sort(self, key: Optional[Callable[[T], str]] = None, reverse: bool = False) -> None:
        tmp = list(zip(self._names, self._values))
        if key is None:
            tmp.sort(reverse=reverse)
        else:
            key_fn = cast(Callable[[T], str], key)
            tmp.sort(key=lambda x: key_fn(x[1]), reverse=reverse)

        self._names = [x[0] for x in tmp]
        self._values = [x[1] for x in tmp]

    def keys(self) -> Collection[str]:
        return self._names

    def values(self) -> Collection[T]:
        return self._values

    def items(self) -> List[Tuple[str, T]]:
        return list(zip(self._names, self._values))

    def __contains__(self, x: T) -> bool:
        return x in self._values

    def __len__(self) -> int:
        return len(self._values)

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
            if abs(key) < -len(self._values) or key >= len(self._values):
                # we want to raise a KeyError instead of an IndexError
                # if the index is out of range...
                raise KeyError(f"Tried to access item {key} of a NamedItemList "
                               f"of length {len(self)}")

            return self._values[key]
        elif isinstance(key, slice):
            # for slices, we unfortunately have to ignore the typing
            # because if the key is a slice, we cannot return a single
            # item. (alternatively, the return type of this method
            # could be defined as Union[T, List[T]], but this leads
            # mypy to produce *many* spurious and hard to fix errors.
            return self._values[key]
        else:
            return self.__dict__[key]

    def get(self, key: Union[int, str], default: Optional[T] = None) -> Optional[T]:
        if isinstance(key, int):
            if abs(key) < -len(self._values) or key >= len(self._values):
                return default

            return self._values[key]
        else:
            return cast(Optional[T], self.__dict__.get(key, default))

    def __eq__(self, other: object) -> bool:
        """
        Named item lists are equal if the underlying lists are equal.
        Note that this does not consider the map `item_to_name_fn`.
        """
        if not isinstance(other, NamedItemList):
            return False
        else:
            return self._names == other._names and self._values == other._values

    # -> Iterator[T]: # <- this leads to *many* type checking errors
    def __iter__(self):
        return iter(self._values)

    def __str__(self) -> str:
        return f"[{', '.join([x for x in self._names])}]"

    def __repr__(self) -> str:
        return self.__str__()


def short_name_as_key(obj: OdxNamed) -> str:
    """Retrieve an object's `short_name` attribute into a valid python identifier.

    Although short names are almost identical to python identifiers,
    their first character is allowed to be a number. This method
    prepends an underscore to such such shortnames.
    """
    if not isinstance(obj, OdxNamed):
        odxraise()
    sn = obj.short_name
    if not isinstance(sn, str):
        odxraise()

    odxassert(
        sn.isidentifier(),
        message=("For NamedItemList objects to work properly, "
                 "all item names must be valid python identifiers."
                 f"Encountered name '{sn}' which is not an identifier!"),
    )

    if sn[0].isdigit():
        return f"_{sn}"

    # make sure that the name of the item in question is not a
    # python keyword (this would lead to syntax errors)
    if iskeyword(sn):
        return f"{sn}_"

    return sn


class NamedItemList(Generic[TNamed], ItemList[TNamed]):

    def _get_item_key(self, obj: OdxNamed) -> str:
        return short_name_as_key(obj)
