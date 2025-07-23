# SPDX-License-Identifier: MIT
import warnings
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree

from .basecomparam import BaseComparam
from .comparam import Comparam
from .complexcomparam import ComplexComparam, ComplexValue, create_complex_value_from_et
from .description import Description
from .exceptions import OdxWarning, odxraise, odxrequire
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class ComparamInstance:
    """
    This class represents a communication parameter.

    Be aware that the ODX specification calls this class COMPARAM-REF!
    """
    value: str | ComplexValue
    description: Description | None = None
    protocol_snref: str | None = None
    prot_stack_snref: str | None = None
    spec_ref: OdxLinkRef

    @property
    def spec(self) -> BaseComparam:
        return self._spec

    @property
    def short_name(self) -> str:
        return self.spec.short_name

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ComparamInstance":
        spec_ref = odxrequire(OdxLinkRef.from_et(et_element, context))

        # ODX standard v2.0.0 defined only VALUE. ODX v2.0.1 decided
        # to break things and change it to a choice between SIMPLE-VALUE
        # and COMPLEX-VALUE
        value: str | list[str | ComplexValue]
        if et_element.find("VALUE") is not None:
            value = odxrequire(et_element.findtext("VALUE"))
        elif et_element.find("SIMPLE-VALUE") is not None:
            value = odxrequire(et_element.findtext("SIMPLE-VALUE"))
        else:
            value = create_complex_value_from_et(odxrequire(et_element.find("COMPLEX-VALUE")))

        description = Description.from_et(et_element.find("DESC"), context)

        protocol_snref = None
        if (psnref_elem := et_element.find("PROTOCOL-SNREF")) is not None:
            protocol_snref = psnref_elem.get("SHORT-NAME")

        prot_stack_snref = None
        if (psnref_elem := et_element.find("PROT-STACK-SNREF")) is not None:
            prot_stack_snref = psnref_elem.get("SHORT-NAME")

        return ComparamInstance(
            value=value,
            spec_ref=spec_ref,
            description=description,
            protocol_snref=protocol_snref,
            prot_stack_snref=prot_stack_snref,
        )

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._spec = odxlinks.resolve(self.spec_ref, BaseComparam)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        pass

    def get_value(self) -> str:
        """Retrieve the value of a simple communication parameter

        This takes the default value of the comparam (if any) into
        account.
        """

        if not isinstance(self.spec, Comparam):
            odxraise()

        result: Any = None
        if self.value:
            result = self.value
        else:
            result = self.spec.physical_default_value

        if not isinstance(result, str):
            odxraise()

        return result

    def get_subvalue(self, subparam_name: str) -> str | None:
        """Retrieve the value of a complex communication parameter's sub-parameter by name

        This takes the default value of the comparam (if any) into
        account.
        """
        comparam_spec = self.spec
        if not isinstance(comparam_spec, ComplexComparam):
            odxraise()

        value_list = self.value
        if not isinstance(value_list, list):
            warnings.warn(
                f"The values of complex communication parameter "
                f"'{self.short_name}' are not specified "
                f"correctly.",
                OdxWarning,
                stacklevel=1,
            )
            return None

        name_list = [cp.short_name for cp in comparam_spec.subparams]
        try:
            idx = name_list.index(subparam_name)
            subparam = comparam_spec.subparams[idx]
        except ValueError:
            warnings.warn(
                f"Communication parameter '{self.short_name}' "
                f"does not specify a '{subparam_name}' sub-parameter.",
                OdxWarning,
                stacklevel=1,
            )
            return None

        result = value_list[idx]
        if result is None and isinstance(subparam, (Comparam, ComplexComparam)):
            result = subparam.physical_default_value
        if not isinstance(result, str):
            odxraise()

        return result
