# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .basecomparam import BaseComparam
from .complexcomparam import ComplexValue, create_complex_value_from_et
from .description import Description
from .exceptions import odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class LinkComparamRef(OdxLinkRef):
    """This class is very similar to ComparamInstance, but it is used
    in the context of vehicle info specifications"""

    # exactly one of the following two attributes must be not None
    simple_value: str | None = None
    complex_value: ComplexValue | None = None

    description: Description | None = None

    @property
    def spec(self) -> BaseComparam:
        return self._spec

    @property
    def short_name(self) -> str:
        return self._spec.short_name

    @staticmethod
    def from_et(  # type: ignore[override]
            et_element: ElementTree.Element, context: OdxDocContext) -> "LinkComparamRef":
        kwargs = dataclass_fields_asdict(odxrequire(OdxLinkRef.from_et(et_element, context)))

        simple_value = et_element.findtext("SIMPLE-VALUE")
        complex_value = None
        if (cv_elem := et_element.find("COMPLEX-VALUE")) is not None:
            complex_value = create_complex_value_from_et(cv_elem)
        description = Description.from_et(et_element.find("DESC"), context)

        return LinkComparamRef(
            simple_value=simple_value,
            complex_value=complex_value,
            description=description,
            **kwargs)

    def __post_init__(self) -> None:
        self._spec: BaseComparam

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._spec = odxlinks.resolve(self, BaseComparam)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass
