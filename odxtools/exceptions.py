# SPDX-License-Identifier: MIT
from typing import TYPE_CHECKING, NoReturn, Optional, Type, TypeVar

from .globals import logger


class OdxError(Exception):
    """Any error that happens during interacting with diagnostic objects."""


class EncodeError(Warning, OdxError):
    """Encoding of a message to raw data failed."""


class DecodeError(Warning, OdxError):
    """Decoding raw data failed."""


class OdxWarning(Warning):
    """Any warning that happens during interacting with diagnostic objects."""


#: Specify whether violations of the ODX specification or failed
#: assumptions in the ODX library code should cause the routine in
#: question to abort or whether it should continue anyway. Be aware that
#: in non-strict mode, the behavior of odxtools is undefined and it
#: might start eating children...
strict_mode = True


def odxraise(message: Optional[str] = None, error_type: Type[Exception] = OdxError) -> NoReturn:
    """
    Raise an exception but only if in strict mode.

    Also, convince type checkers that the exception is always raised.
    """
    if TYPE_CHECKING or strict_mode:
        if message is None:
            raise error_type()
        else:
            raise error_type(message)
    elif message is not None:
        logger.warn(message)


def odxassert(condition: bool,
              message: Optional[str] = None,
              error_type: Type[Exception] = OdxError) -> None:
    """
    This method works similar as the build-in `assert` statement

    The differences are that instead of raising an `AssertationError`,
    an `OdxError` is raised by default and that is possible to not
    raise any exception by setting `odxtools.exceptions.strict_mode` to
    `False`. The latter is convenient when having to deal with files
    that do not comply to the ODX specification, but it may lead to
    undefined behavior. (Use the non-strict mode with great care.)
    """
    if not condition:
        odxraise(message, error_type)


T = TypeVar("T")


def odxrequire(obj: Optional[T], message: Optional[str] = None) -> T:
    """This function ensures that an object required by the ODX
    specification is actually present.

    In other words, that the object in question is not `None`. If such
    a mandatory object is not present, an `OdxError` is raised if the
    `odxtools.exceptions.strict_mode` flag is `True`. (Note that this
    function is pretty useful for type checking.)
    """
    if obj is None:
        odxraise(message)

    return obj
