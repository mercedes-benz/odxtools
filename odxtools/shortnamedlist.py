# SPDX-License-Identifier: MIT
from typing import Iterable, Optional, TypeVar

from .nameditemlist import NamedItemList
from .utils import short_name_as_id

T = TypeVar("T")


class ShortNamedList(NamedItemList[T]):
    """This is a shorthand for ``NamedItemList(short_name_as_id)``

    i.e., it is an list-like collections of objects that where the
    individual items can be accessed using
    ``snlist.{item_short_name}``. In odxtools, this is by far the most
    common usage scenario for ``NamedItemList``...
    """

    def __init__(self, input_list: Optional[Iterable[T]] = None):
        super().__init__(short_name_as_id, input_list)
