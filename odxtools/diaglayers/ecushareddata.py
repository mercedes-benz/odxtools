# SPDX-License-Identifier: MIT
from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Union, cast
from xml.etree import ElementTree

from ..diagvariable import DiagVariable
from ..exceptions import odxassert
from ..nameditemlist import NamedItemList
from ..odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkRef
from ..snrefcontext import SnRefContext
from ..variablegroup import VariableGroup
from .diaglayer import DiagLayer
from .ecushareddataraw import EcuSharedDataRaw

if TYPE_CHECKING:
    from .database import Database


@dataclass
class EcuSharedData(DiagLayer):
    """This is a diagnostic layer for data shared across others
    """

    @property
    def ecu_shared_data_raw(self) -> EcuSharedDataRaw:
        return cast(EcuSharedDataRaw, self.diag_layer_raw)

    @property
    def diag_variables_raw(self) -> List[Union[OdxLinkRef, DiagVariable]]:
        return self.ecu_shared_data_raw.diag_variables_raw

    @property
    def diag_variables(self) -> NamedItemList[DiagVariable]:
        return self.ecu_shared_data_raw.diag_variables

    @property
    def variable_groups(self) -> NamedItemList[VariableGroup]:
        return self.ecu_shared_data_raw.variable_groups

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "EcuSharedData":
        ecu_shared_data_raw = EcuSharedDataRaw.from_et(et_element, doc_frags)

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

        # this attribute may be removed later. it is currently
        # required to properly deal with auxiliary files within the
        # diagnostic layer.
        self._database = database

        #####
        # resolve all SNREFs. TODO: We allow SNREFS to objects that
        # were inherited by the diaglayer. This might not be allowed
        # by the spec (So far, I haven't found any definitive
        # statement...)
        #####
        context = SnRefContext(database=database)
        context.diag_layer = self
        self._resolve_snrefs(context)
        context.diag_layer = None

    def __deepcopy__(self, memo: Dict[int, Any]) -> Any:
        """Create a deep copy of the protocol layer

        Note that the copied diagnostic layer is not fully
        initialized, so `_finalize_init()` should to be called on it
        before it can be used normally.
        """

        result = super().__deepcopy__(memo)

        # note that the self.ecu_shared_data_raw object is *not* copied at
        # this place because the attribute points to the same object
        # as self.diag_layer_raw.
        result.ecu_shared_data_raw = deepcopy(self.ecu_shared_data_raw, memo)

        return result
