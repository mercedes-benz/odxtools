# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast
from xml.etree import ElementTree

from ..diagvariable import DiagVariable
from ..exceptions import odxassert
from ..nameditemlist import NamedItemList
from ..odxdoccontext import OdxDocContext
from ..odxlink import OdxLinkDatabase, OdxLinkRef
from ..snrefcontext import SnRefContext
from ..variablegroup import VariableGroup
from .diaglayer import DiagLayer
from .ecushareddataraw import EcuSharedDataRaw

if TYPE_CHECKING:
    from ..database import Database


@dataclass(kw_only=True)
class EcuSharedData(DiagLayer):
    """This is a diagnostic layer for data shared across others
    """

    @property
    def ecu_shared_data_raw(self) -> EcuSharedDataRaw:
        return cast(EcuSharedDataRaw, self.diag_layer_raw)

    @property
    def diag_variables_raw(self) -> list[OdxLinkRef | DiagVariable]:
        return self.ecu_shared_data_raw.diag_variables_raw

    @property
    def diag_variables(self) -> NamedItemList[DiagVariable]:
        return self.ecu_shared_data_raw.diag_variables

    @property
    def variable_groups(self) -> NamedItemList[VariableGroup]:
        return self.ecu_shared_data_raw.variable_groups

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "EcuSharedData":
        ecu_shared_data_raw = EcuSharedDataRaw.from_et(et_element, context)

        return EcuSharedData(diag_layer_raw=ecu_shared_data_raw)

    def __post_init__(self) -> None:
        super().__post_init__()

        odxassert(
            isinstance(self.diag_layer_raw, EcuSharedDataRaw),
            "The raw diagnostic layer passed to EcuSharedData "
            "must be a EcuSharedDataRaw")

    def _finalize_init(self, database: "Database", odxlinks: OdxLinkDatabase) -> None:
        """This method makes sure that all references in sub-objects
        of the ECU shared data layer are resolved

        In contrast to hierarchy element layers, ECU shared data
        layers do not need to deal with inheritance...

        """

        #####
        # resolve all SNREFs. TODO: We allow SNREFS to objects that
        # were inherited by the diaglayer. This might not be allowed
        # by the spec (So far, I haven't found any definitive
        # statement...)
        #####
        context = SnRefContext(database=database, use_weakrefs=odxlinks.use_weakrefs)
        context.diag_layer = self
        self._resolve_snrefs(context)
        context.diag_layer = None
