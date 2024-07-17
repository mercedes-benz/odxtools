# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union, cast
from xml.etree import ElementTree

from typing_extensions import override

from .compumethods.compumethod import CompuMethod
from .compumethods.createanycompumethod import create_any_compu_method_from_et
from .createanydiagcodedtype import create_any_diag_coded_type_from_et
from .decodestate import DecodeState
from .diagcodedtype import DiagCodedType
from .diagnostictroublecode import DiagnosticTroubleCode
from .dopbase import DopBase
from .encodestate import EncodeState
from .exceptions import DecodeError, EncodeError, odxassert, odxraise, odxrequire
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import ParameterValue, odxstr_to_bool
from .physicaltype import PhysicalType
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass
class DtcDop(DopBase):
    """A DOP describing a diagnostic trouble code"""

    diag_coded_type: DiagCodedType
    physical_type: PhysicalType
    compu_method: CompuMethod
    dtcs_raw: List[Union[DiagnosticTroubleCode, OdxLinkRef]]
    linked_dtc_dop_refs: List[OdxLinkRef]
    is_visible_raw: Optional[bool]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "DtcDop":
        """Reads a DTC-DOP."""
        kwargs = dataclass_fields_asdict(DopBase.from_et(et_element, doc_frags))

        diag_coded_type = create_any_diag_coded_type_from_et(
            odxrequire(et_element.find("DIAG-CODED-TYPE")), doc_frags)
        physical_type = PhysicalType.from_et(
            odxrequire(et_element.find("PHYSICAL-TYPE")), doc_frags)
        compu_method = create_any_compu_method_from_et(
            odxrequire(et_element.find("COMPU-METHOD")),
            doc_frags,
            internal_type=diag_coded_type.base_data_type,
            physical_type=physical_type.base_data_type,
        )
        dtcs_raw: List[Union[DiagnosticTroubleCode, OdxLinkRef]] = []
        if (dtcs_elem := et_element.find("DTCS")) is not None:
            for dtc_proxy_elem in dtcs_elem:
                if dtc_proxy_elem.tag == "DTC":
                    dtcs_raw.append(DiagnosticTroubleCode.from_et(dtc_proxy_elem, doc_frags))
                elif dtc_proxy_elem.tag == "DTC-REF":
                    dtcs_raw.append(OdxLinkRef.from_et(dtc_proxy_elem, doc_frags))

        # TODO: NOT-INHERITED-DTC-SNREFS
        linked_dtc_dop_refs = [
            OdxLinkRef.from_et(dtc_ref_elem, doc_frags)
            for dtc_ref_elem in et_element.iterfind("LINKED-DTC-DOPS/"
                                                    "LINKED-DTC-DOP/"
                                                    "DTC-DOP-REF")
        ]
        is_visible_raw = odxstr_to_bool(et_element.get("IS-VISIBLE"))

        return DtcDop(
            diag_coded_type=diag_coded_type,
            physical_type=physical_type,
            compu_method=compu_method,
            dtcs_raw=dtcs_raw,
            linked_dtc_dop_refs=linked_dtc_dop_refs,
            is_visible_raw=is_visible_raw,
            **kwargs)

    @property
    def dtcs(self) -> NamedItemList[DiagnosticTroubleCode]:
        return self._dtcs

    @property
    def is_visible(self) -> bool:
        return self.is_visible_raw is True

    @property
    def linked_dtc_dops(self) -> NamedItemList["DtcDop"]:
        return self._linked_dtc_dops

    @override
    def decode_from_pdu(self, decode_state: DecodeState) -> ParameterValue:

        int_trouble_code = self.diag_coded_type.decode_from_pdu(decode_state)

        if not self.compu_method.is_valid_internal_value(int_trouble_code):
            # TODO: How to prevent this?
            odxraise(
                f"DTC-DOP {self.short_name} could not convert the coded value "
                f" {repr(int_trouble_code)} to physical type {self.physical_type.base_data_type}.",
                DecodeError)
            return

        trouble_code = self.compu_method.convert_internal_to_physical(int_trouble_code)

        assert isinstance(trouble_code, int)

        dtcs = [x for x in self.dtcs if x.trouble_code == trouble_code]

        odxassert(len(dtcs) < 2, f"Multiple matching DTCs for trouble code 0x{trouble_code:06x}")

        if len(dtcs) == 1:
            # we found exactly one described DTC
            return dtcs[0]

        # the DTC was not specified. This probably means that the
        # diagnostic description file is incomplete.
        odxraise(
            f"Encountered DTC 0x{trouble_code:06x} which has not been defined "
            f"by the database", DecodeError)

        return DiagnosticTroubleCode(
            trouble_code=trouble_code,
            odx_id=cast(OdxLinkId, None),
            short_name=f'DTC_{trouble_code:06x}',
            long_name=None,
            description=None,
            text=None,
            display_trouble_code=None,
            level=None,
            is_temporary_raw=None,
            sdgs=[],
        )

    def convert_to_numerical_trouble_code(self, dtc_value: ParameterValue) -> int:
        if isinstance(dtc_value, DiagnosticTroubleCode):
            return dtc_value.trouble_code
        elif isinstance(dtc_value, int):
            # assume that physical value is the trouble_code
            return dtc_value
        elif isinstance(dtc_value, str):
            # assume that physical value is the short_name
            dtcs = [dtc for dtc in self.dtcs if dtc.short_name == dtc_value]
            if len(dtcs) != 1:
                odxraise(f"No DTC named {dtc_value} found for DTC-DOP "
                         f"{self.short_name}.", EncodeError)
                return cast(int, None)

            return dtcs[0].trouble_code
        else:
            odxraise(
                f"The DTC-DOP {self.short_name} expected a"
                f" diagnostic trouble code but got {type(dtc_value).__name__}", EncodeError)
            return cast(int, None)

    @override
    def encode_into_pdu(self, physical_value: Optional[ParameterValue],
                        encode_state: EncodeState) -> None:
        if physical_value is None:
            odxraise(f"No DTC specified", EncodeError)
            return

        trouble_code = self.convert_to_numerical_trouble_code(physical_value)

        internal_trouble_code = int(self.compu_method.convert_physical_to_internal(trouble_code))

        found = False
        for dtc in self.dtcs:
            if internal_trouble_code == dtc.trouble_code:
                found = True
                break

        if not found:
            odxraise(
                f"Unknown diagnostic trouble code {physical_value!r} "
                f"(0x{internal_trouble_code: 06x}) specified", EncodeError)

        self.diag_coded_type.encode_into_pdu(internal_trouble_code, encode_state)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()

        for dtc_proxy in self.dtcs_raw:
            if isinstance(dtc_proxy, DiagnosticTroubleCode):
                odxlinks.update(dtc_proxy._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

        self._dtcs = NamedItemList[DiagnosticTroubleCode]()
        for dtc_proxy in self.dtcs_raw:
            if isinstance(dtc_proxy, DiagnosticTroubleCode):
                dtc_proxy._resolve_odxlinks(odxlinks)
                self._dtcs.append(dtc_proxy)
            elif isinstance(dtc_proxy, OdxLinkRef):
                dtc = odxlinks.resolve(dtc_proxy, DiagnosticTroubleCode)
                self._dtcs.append(dtc)

        linked_dtc_dops = [odxlinks.resolve(x, DtcDop) for x in self.linked_dtc_dop_refs]
        self._linked_dtc_dops = NamedItemList(linked_dtc_dops)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        for dtc_proxy in self.dtcs_raw:
            if isinstance(dtc_proxy, DiagnosticTroubleCode):
                dtc_proxy._resolve_snrefs(context)
