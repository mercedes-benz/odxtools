# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
from dataclasses import dataclass, field
from itertools import chain
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Union, cast

from .admindata import AdminData
from .audience import Audience
from .dataobjectproperty import DopBase
from .exceptions import DecodeError, EncodeError
from .functionalclass import FunctionalClass
from .globals import logger
from .message import Message
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .odxtypes import odxstr_to_bool
from .specialdata import SpecialDataGroup, create_sdgs_from_et
from .utils import create_description_from_et, short_name_as_id

if TYPE_CHECKING:
    from .diaglayer import DiagLayer

DiagClassType = Literal[
    "STARTCOMM",
    "STOPCOMM",
    "VARIANTIDENTIFICATION",
    "READ-DYN-DEFINED-MESSAGE",
    "DYN-DEF-MESSAGE",
    "CLEAR-DYN-DEF-MESSAGE",
]


@dataclass
class InputParam:
    short_name: str
    dop_base_ref: OdxLinkRef
    long_name: Optional[str]
    description: Optional[str]
    oid: Optional[str]
    semantic: Optional[str]
    physical_default_value: Optional[str]

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "InputParam":
        short_name = et_element.findtext("SHORT-NAME")
        assert short_name is not None
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))
        dop_base_ref = OdxLinkRef.from_et(et_element.find("DOP-BASE-REF"), doc_frags)
        assert dop_base_ref is not None
        physical_default_value = et_element.findtext("PHYSICAL-DEFAULT-VALUE")

        semantic = et_element.get("SEMANTIC")
        oid = et_element.get("OID")

        return InputParam(
            short_name=short_name,
            long_name=long_name,
            description=description,
            dop_base_ref=dop_base_ref,
            physical_default_value=physical_default_value,
            semantic=semantic,
            oid=oid,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._dop = odxlinks.resolve(self.dop_base_ref, DopBase)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass

    @property
    def dop(self) -> DopBase:
        """The data object property describing this parameter."""
        return self._dop


@dataclass
class OutputParam:
    odx_id: OdxLinkId
    short_name: str
    dop_base_ref: OdxLinkRef
    long_name: Optional[str]
    description: Optional[str]
    oid: Optional[str]
    semantic: Optional[str]

    def __post_init__(self) -> None:
        self._dop: Optional[DopBase] = None

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "OutputParam":

        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None
        short_name = et_element.findtext("SHORT-NAME")
        assert short_name is not None
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))
        dop_base_ref = OdxLinkRef.from_et(et_element.find("DOP-BASE-REF"), doc_frags)
        assert dop_base_ref is not None

        semantic = et_element.get("SEMANTIC")
        oid = et_element.get("OID")

        return OutputParam(
            odx_id=odx_id,
            short_name=short_name,
            long_name=long_name,
            description=description,
            dop_base_ref=dop_base_ref,
            semantic=semantic,
            oid=oid,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._dop = odxlinks.resolve(self.dop_base_ref)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass

    @property
    def dop(self) -> Optional[DopBase]:
        """The data object property describing this parameter."""
        return self._dop


@dataclass
class NegOutputParam:
    short_name: str
    dop_base_ref: OdxLinkRef
    long_name: Optional[str]
    description: Optional[str]

    def __post_init__(self) -> None:
        self._dop: Optional[DopBase] = None

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "NegOutputParam":

        short_name = et_element.findtext("SHORT-NAME")
        assert short_name is not None
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))
        dop_base_ref = OdxLinkRef.from_et(et_element.find("DOP-BASE-REF"), doc_frags)
        assert dop_base_ref is not None

        return NegOutputParam(
            short_name=short_name,
            long_name=long_name,
            description=description,
            dop_base_ref=dop_base_ref,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._dop = odxlinks.resolve(self.dop_base_ref)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass

    @property
    def dop(self) -> Optional[DopBase]:
        """The data object property describing this parameter."""
        return self._dop


@dataclass
class ProgCode:
    """A reference to code that is executed by a single ECU job"""

    code_file: str
    syntax: Literal["JAVA", "CLASS", "JAR"]
    revision: str
    encryption: Optional[str]
    entrypoint: Optional[str]
    library_refs: List[OdxLinkRef]

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "ProgCode":
        code_file = et_element.findtext("CODE-FILE")

        encryption = et_element.findtext("ENCRYPTION")

        syntax = et_element.findtext("SYNTAX")
        revision = et_element.findtext("REVISION")

        entrypoint = et_element.findtext("ENTRYPOINT")

        library_refs = []
        for el in et_element.iterfind("LIBRARY-REFS/LIBRARY-REF"):
            ref = OdxLinkRef.from_et(el, doc_frags)
            assert ref is not None
            library_refs.append(ref)

        return ProgCode(
            code_file=code_file,
            syntax=syntax,
            revision=revision,
            encryption=encryption,
            entrypoint=entrypoint,
            library_refs=library_refs,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        # TODO: Libraries are currently not internalized.
        #       Once they are internalized, resolve the `library_refs` references here.
        pass

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass


@dataclass
class SingleEcuJob:
    """A single ECU job is a diagnostic communication primitive.

    A single ECU job is more complex than a diagnostic service and is not provided natively by the ECU.
    In particular, the job is defined in external programs which are referenced by the attribute `.prog_codes`.

    In contrast to "multiple ECU jobs", a single ECU job only does service calls to a single ECU.

    Single ECU jobs are defined in section 7.3.5.7 of the ASAM MCD-2 standard.

    TODO: The following xml attributes are not internalized yet:
          PROTOCOL-SNREFS, RELATED-DIAG-COMM-REFS, PRE-CONDITION-STATE-REFS, STATE-TRANSITION-REFS
    """

    odx_id: OdxLinkId
    short_name: str
    prog_codes: List[ProgCode]
    """Pointers to the code that is executed when calling this job."""
    # optional xsd:elements inherited from DIAG-COMM (and thus shared with DIAG-SERVICE)
    oid: Optional[str]
    long_name: Optional[str]
    description: Optional[str]
    admin_data: Optional[AdminData]
    functional_class_refs: List[OdxLinkRef]
    audience: Optional[Audience]
    # optional xsd:elements specific to SINGLE-ECU-JOB
    # cast(...) just tells the type checker to pretend it's a list...
    input_params: Union[NamedItemList[InputParam], List[InputParam]]
    output_params: Union[NamedItemList[OutputParam], List[OutputParam]]
    neg_output_params: Union[NamedItemList[NegOutputParam], List[NegOutputParam]]
    # xsd:attributes inherited from DIAG-COMM (and thus shared with DIAG-SERVICE)
    semantic: Optional[str]
    diagnostic_class: Optional[DiagClassType]
    is_mandatory_raw: Optional[bool]
    is_executable_raw: Optional[bool]
    is_final_raw: Optional[bool]
    sdgs: List[SpecialDataGroup]

    @property
    def is_mandatory(self):
        return self.is_mandatory_raw == True

    @property
    def is_executable(self):
        return self.is_executable_raw in (None, True)

    @property
    def is_final(self):
        return self.is_final_raw == True

    def __post_init__(self) -> None:
        if not self.functional_class_refs:
            self.functional_class_refs = []
        self._functional_classes: Optional[NamedItemList[FunctionalClass]] = None

        # Replace None attributes by empty lists
        if not self.input_params:
            self.input_params = NamedItemList(short_name_as_id)
        if not self.output_params:
            self.output_params = NamedItemList(short_name_as_id)
        if not self.neg_output_params:
            self.neg_output_params = NamedItemList(short_name_as_id)

    @staticmethod
    def from_et(et_element, doc_frags: List[OdxDocFragment]) -> "SingleEcuJob":

        logger.info(f"Parsing service based on ET DiagService element: {et_element}")
        odx_id = OdxLinkId.from_et(et_element, doc_frags)
        assert odx_id is not None
        short_name = et_element.findtext("SHORT-NAME")
        assert short_name is not None
        long_name = et_element.findtext("LONG-NAME")
        description = create_description_from_et(et_element.find("DESC"))
        admin_data = AdminData.from_et(et_element.find("ADMIN-DATA"), doc_frags)
        semantic = et_element.get("SEMANTIC")

        functional_class_refs = []
        for el in et_element.iterfind("FUNCT-CLASS-REFS/FUNCT-CLASS-REF"):
            ref = OdxLinkRef.from_et(el, doc_frags)
            assert ref is not None
            functional_class_refs.append(ref)

        prog_codes = [
            ProgCode.from_et(pc_elem, doc_frags)
            for pc_elem in et_element.iterfind("PROG-CODES/PROG-CODE")
        ]

        if et_element.find("AUDIENCE"):
            audience = Audience.from_et(et_element.find("AUDIENCE"), doc_frags)
        else:
            audience = None

        input_params = [
            InputParam.from_et(el, doc_frags)
            for el in et_element.iterfind("INPUT-PARAMS/INPUT-PARAM")
        ]
        output_params = [
            OutputParam.from_et(el, doc_frags)
            for el in et_element.iterfind("OUTPUT-PARAMS/OUTPUT-PARAM")
        ]
        neg_output_params = [
            NegOutputParam.from_et(el, doc_frags)
            for el in et_element.iterfind("NEG-OUTPUT-PARAMS/NEG-OUTPUT-PARAM")
        ]

        # Read boolean flags. Note that the "else" clause contains the default value.
        is_mandatory_raw = odxstr_to_bool(et_element.get("IS-MANDATORY"))
        is_executable_raw = odxstr_to_bool(et_element.get("IS-MANDATORY"))
        is_final_raw = odxstr_to_bool(et_element.get("IS-FINAL"))

        sdgs = create_sdgs_from_et(et_element.find("SDGS"), doc_frags)

        return SingleEcuJob(
            odx_id=odx_id,
            oid=None,
            short_name=short_name,
            long_name=long_name,
            description=description,
            admin_data=admin_data,
            prog_codes=prog_codes,
            semantic=semantic,
            audience=audience,
            functional_class_refs=functional_class_refs,
            diagnostic_class=None,
            input_params=input_params,
            output_params=output_params,
            neg_output_params=neg_output_params,
            is_mandatory_raw=is_mandatory_raw,
            is_executable_raw=is_executable_raw,
            is_final_raw=is_final_raw,
            sdgs=sdgs,
        )

    @property
    def functional_classes(self) -> Optional[NamedItemList[FunctionalClass]]:
        """The functional classes referenced by this job.
        This is None iff the references were not resolved.
        """
        return self._functional_classes

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = {self.odx_id: self}

        for obj in chain(self.prog_codes, self.input_params, self.output_params,
                         self.neg_output_params, self.sdgs):
            result.update(obj._build_odxlinks())

        if self.admin_data:
            result.update(self.admin_data._build_odxlinks())

        if self.audience:
            result.update(self.audience._build_odxlinks())

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        for code in self.prog_codes:
            code._resolve_odxlinks(odxlinks)

        # Resolve references to functional classes
        self._functional_classes = NamedItemList[FunctionalClass](short_name_as_id, [])
        for fc_ref in self.functional_class_refs:
            fc = odxlinks.resolve(fc_ref)
            if isinstance(fc, FunctionalClass):
                self._functional_classes.append(fc)
            else:
                logger.warning(f"Functional class ID {fc_ref!r} resolved to {fc!r}.")

        for obj in chain(self.prog_codes, self.input_params, self.output_params,
                         self.neg_output_params, self.sdgs):
            obj._resolve_odxlinks(odxlinks)

        # Resolve references of admin data
        if self.admin_data:
            self.admin_data._resolve_odxlinks(odxlinks)

        # Resolve references of audience
        if self.audience:
            self.audience._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        for obj in chain(self.prog_codes, self.input_params, self.output_params,
                         self.neg_output_params, self.sdgs):
            obj._resolve_snrefs(diag_layer)

        # Resolve references of admin data
        if self.admin_data:
            self.admin_data._resolve_snrefs(diag_layer)

        # Resolve references of audience
        if self.audience:
            self.audience._resolve_snrefs(diag_layer)

    def decode_message(self, message: bytes) -> Message:
        """This function's signature matches `DiagService.decode_message`
        and only raises an informative error.
        """
        raise DecodeError(
            f"Single ECU jobs are completely executed on the tester and thus cannot be decoded."
            f" You tried to decode a response for the job {self.odx_id}.")

    def encode_request(self, **params):
        """This function's signature matches `DiagService.encode_request`
        and only raises an informative error.
        """
        raise EncodeError(
            f"Single ECU jobs are completely executed on the tester and thus cannot be encoded."
            f" You tried to encode a request for the job {self.odx_id}.")

    def encode_positive_response(self, coded_request, response_index=0, **params):
        """This function's signature matches `DiagService.encode_positive_response`
        and only raises an informative error.
        """
        raise EncodeError(
            f"Single ECU jobs are completely executed on the tester and thus cannot be encoded."
            f" You tried to encode a response for the job {self.odx_id}.")

    def encode_negative_response(self, coded_request, response_index=0, **params):
        """This function's signature matches `DiagService.encode_negative_response`
        and only raises an informative error.
        """
        raise EncodeError(
            f"Single ECU jobs are completely executed on the tester and thus cannot be encoded."
            f" You tried to encode the job {self.odx_id}.")

    def __call__(self, **params) -> bytes:
        raise EncodeError(
            f"Single ECU jobs are completely executed on the tester and thus cannot be encoded."
            f" You tried to call the job {self.odx_id}.")

    def __hash__(self) -> int:
        return hash(self.odx_id)
