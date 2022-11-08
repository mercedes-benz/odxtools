# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Union, cast

from .utils import short_name_as_id
from .dataobjectproperty import DopBase
from .audience import Audience, read_audience_from_odx
from .functionalclass import FunctionalClass
from .utils import read_description_from_odx
from .odxlink import OdxLinkRef, OdxLinkId, OdxLinkDatabase, OdxDocFragment
from .nameditemlist import NamedItemList
from .globals import logger
from .exceptions import EncodeError, DecodeError
from .message import Message

DiagClassType = Literal["STARTCOMM",
                        "STOPCOMM",
                        "VARIANTIDENTIFICATION",
                        "READ-DYN-DEFINED-MESSAGE",
                        "DYN-DEF-MESSAGE",
                        "CLEAR-DYN-DEF-MESSAGE"]


@dataclass
class InputParam:
    short_name: str
    dop_base_ref: OdxLinkRef
    long_name: Optional[str] = None
    description: Optional[str] = None
    oid: Optional[str] = None
    semantic: Optional[str] = None
    physical_default_value: Optional[str] = None

    def __post_init__(self) -> None:
        self._dop: Optional[DopBase] = None

    def _resolve_references(self, odxlinks: OdxLinkDatabase) -> None:
        self._dop = odxlinks.resolve(self.dop_base_ref)

    @property
    def dop(self) -> Optional[DopBase]:
        """The data object property describing this parameter."""
        return self._dop


@dataclass
class OutputParam:
    odx_id: OdxLinkId
    short_name: str
    dop_base_ref: OdxLinkRef
    long_name: Optional[str] = None
    description: Optional[str] = None
    oid: Optional[str] = None
    semantic: Optional[str] = None

    def __post_init__(self) -> None:
        self._dop: Optional[DopBase] = None

    def _resolve_references(self, odxlinks: OdxLinkDatabase) -> None:
        self._dop = odxlinks.resolve(self.dop_base_ref)

    @property
    def dop(self) -> Optional[DopBase]:
        """The data object property describing this parameter."""
        return self._dop


@dataclass
class NegOutputParam:
    short_name: str
    dop_base_ref: OdxLinkRef
    long_name: Optional[str] = None
    description: Optional[str] = None

    def __post_init__(self) -> None:
        self._dop: Optional[DopBase] = None

    def _resolve_references(self, odxlinks: OdxLinkDatabase) -> None:
        self._dop = odxlinks.resolve(self.dop_base_ref)

    @property
    def dop(self) -> Optional[DopBase]:
        """The data object property describing this parameter."""
        return self._dop


@dataclass
class ProgCode:
    """A reference to code that is executed by a single ECU job
    """
    code_file: str
    syntax: Literal["JAVA", "CLASS", "JAR"]
    revision: str
    encryption: Optional[str] = None
    entrypoint: Optional[str] = None
    library_refs: List[OdxLinkRef] = field(default_factory=list)

    def __post_init__(self):
        if not self.library_refs:
            self.library_refs = []

    def _resolve_references(self, odxlinks: OdxLinkDatabase) -> None:
        # TODO: Libraries are currently not internalized.
        #       Once they are internalized, resolve the references `library_refs` here.
        pass


@dataclass
class SingleEcuJob:
    """A single ECU job is a diagnostic communication primitive.

    A single ECU job is more complex than a diagnostic service and is not provided natively by the ECU.
    In particular, the job is defined in external programs which are referenced by the attribute `.prog_codes`.

    In contrast to "multiple ECU jobs", a single ECU job only does service calls to a single ECU.

    Single ECU jobs are defined in section 7.3.5.7 of the ASAM MCD-2 standard.

    TODO: The following xml attributes are not internalized yet:
          ADMIN-DATA, SDGS, PROTOCOL-SNREFS, RELATED-DIAG-COMM-REFS, PRE-CONDITION-STATE-REFS, STATE-TRANSITION-REFS
    """
    odx_id: OdxLinkId
    short_name: str
    prog_codes: List[ProgCode]
    """Pointers to the code that is executed when calling this job."""
    # optional xsd:elements inherited from DIAG-COMM (and thus shared with DIAG-SERVICE)
    oid: Optional[str] = None
    long_name: Optional[str] = None
    description: Optional[str] = None
    functional_class_refs: List[OdxLinkRef] = field(default_factory=list)
    audience: Optional[Audience] = None
    # optional xsd:elements specific to SINGLE-ECU-JOB
    # cast(...) just tells the type checker to pretend it's a list...
    input_params: Union[NamedItemList[InputParam], List[InputParam]] \
        = cast(List[InputParam], field(default_factory=list))
    output_params: Union[NamedItemList[OutputParam], List[OutputParam]] \
        = cast(List[OutputParam], field(default_factory=list))
    neg_output_params: Union[NamedItemList[NegOutputParam], List[NegOutputParam]] \
        = cast(List[NegOutputParam], field(default_factory=list))
    # xsd:attributes inherited from DIAG-COMM (and thus shared with DIAG-SERVICE)
    semantic: Optional[str] = None
    diagnostic_class: Optional[DiagClassType] = None
    is_mandatory: bool = False
    is_executable: bool = True
    is_final: bool = False

    def __post_init__(self) -> None:
        if not self.functional_class_refs:
            self.functional_class_refs = []
        self._functional_classes: Optional[NamedItemList[FunctionalClass]] = None

        # Replace None attributes by empty lists
        if not self.input_params:
            self.input_params = NamedItemList(short_name_as_id, [])
        if not self.output_params:
            self.output_params = NamedItemList(short_name_as_id, [])
        if not self.neg_output_params:
            self.neg_output_params = NamedItemList(short_name_as_id, [])

    @property
    def functional_classes(self) -> Optional[NamedItemList[FunctionalClass]]:
        """The functional classes referenced by this job.
        This is None iff the references were not resolved.
        """
        return self._functional_classes

    def _resolve_references(self, odxlinks: OdxLinkDatabase) -> None:
        # Resolve references to functional classes
        self._functional_classes = NamedItemList[FunctionalClass](
            short_name_as_id, [])
        for fc_ref in self.functional_class_refs:
            fc = odxlinks.resolve(fc_ref)
            if isinstance(fc, FunctionalClass):
                self._functional_classes.append(fc)
            else:
                logger.warning(
                    f"Functional class ID {fc_ref!r} resolved to {fc!r}.")

        # Resolve references of audience
        if self.audience:
            self.audience._resolve_references(odxlinks)

        # Resolve references of params
        params: List[Union[InputParam, OutputParam, NegOutputParam]] \
            = [*self.input_params, *self.output_params, *self.neg_output_params]
        for p in params:
            p._resolve_references(odxlinks)

        for code in self.prog_codes:
            code._resolve_references(odxlinks)

    def decode_message(self, message: Union[bytes, bytearray]) -> Message:
        """This function's signature matches `DiagService.decode_message`
        and only raises an informative error.
        """
        raise DecodeError(f"Single ECU jobs are completely executed on the tester and thus cannot be decoded."
                          f" You tried to decode a response for the job {self.odx_id}.")

    def encode_request(self, **params):
        """This function's signature matches `DiagService.encode_request`
        and only raises an informative error.
        """
        raise EncodeError(f"Single ECU jobs are completely executed on the tester and thus cannot be encoded."
                          f" You tried to encode a request for the job {self.odx_id}.")

    def encode_positive_response(self, coded_request, response_index=0, **params):
        """This function's signature matches `DiagService.encode_positive_response`
        and only raises an informative error.
        """
        raise EncodeError(f"Single ECU jobs are completely executed on the tester and thus cannot be encoded."
                          f" You tried to encode a response for the job {self.odx_id}.")

    def encode_negative_response(self, coded_request, response_index=0, **params):
        """This function's signature matches `DiagService.encode_negative_response`
        and only raises an informative error.
        """
        raise EncodeError(f"Single ECU jobs are completely executed on the tester and thus cannot be encoded."
                          f" You tried to encode the job {self.odx_id}.")

    def __call__(self, **params) -> bytes:
        raise EncodeError(f"Single ECU jobs are completely executed on the tester and thus cannot be encoded."
                          f" You tried to call the job {self.odx_id}.")

    def __hash__(self) -> int:
        return hash(self.odx_id)


def read_prog_code_from_odx(et_element, doc_frags: List[OdxDocFragment]):
    code_file = et_element.find("CODE-FILE").text

    encryption = et_element.findtext("ENCRYPTION")

    syntax = et_element.find("SYNTAX").text
    revision = et_element.find("REVISION").text

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
        library_refs=library_refs
    )


def read_input_param_from_odx(et_element, doc_frags: List[OdxDocFragment]):
    short_name = et_element.findtext("SHORT-NAME")
    assert short_name is not None
    long_name = et_element.findtext("LONG-NAME")
    description = read_description_from_odx(et_element.find("DESC"))
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
        oid=oid
    )


def read_output_param_from_odx(et_element, doc_frags: List[OdxDocFragment]):
    odx_id = OdxLinkId.from_et(et_element, doc_frags)
    assert odx_id is not None
    short_name = et_element.find("SHORT-NAME").text
    assert short_name is not None
    long_name = et_element.findtext("LONG-NAME")
    description = read_description_from_odx(et_element.find("DESC"))
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
        oid=oid
    )


def read_neg_output_param_from_odx(et_element, doc_frags: List[OdxDocFragment]):
    short_name = et_element.find("SHORT-NAME").text
    assert short_name is not None
    long_name = et_element.findtext("LONG-NAME")
    description = read_description_from_odx(et_element.find("DESC"))
    dop_base_ref = OdxLinkRef.from_et(et_element.find("DOP-BASE-REF"), doc_frags)
    assert dop_base_ref is not None

    return NegOutputParam(
        short_name=short_name,
        long_name=long_name,
        description=description,
        dop_base_ref=dop_base_ref
    )


def read_single_ecu_job_from_odx(et_element, doc_frags: List[OdxDocFragment]):
    logger.info(
        f"Parsing service based on ET DiagService element: {et_element}")
    odx_id = OdxLinkId.from_et(et_element, doc_frags)
    assert odx_id is not None
    short_name = et_element.find("SHORT-NAME").text
    assert short_name is not None
    long_name = et_element.findtext("LONG-NAME")
    description = read_description_from_odx(et_element.find("DESC"))
    semantic = et_element.get("SEMANTIC")

    functional_class_refs = []
    for el in et_element.iterfind("FUNCT-CLASS-REFS/FUNCT-CLASS-REF"):
        ref = OdxLinkRef.from_et(el, doc_frags)
        assert ref is not None
        functional_class_refs.append(ref)

    prog_codes = [
        read_prog_code_from_odx(el, doc_frags) for el in et_element.iterfind("PROG-CODES/PROG-CODE")
    ]

    if et_element.find("AUDIENCE"):
        audience = read_audience_from_odx(et_element.find("AUDIENCE"), doc_frags)
    else:
        audience = None

    input_params = [
        read_input_param_from_odx(el, doc_frags) for el in et_element.iterfind("INPUT-PARAMS/INPUT-PARAM")
    ]
    output_params = [
        read_output_param_from_odx(el, doc_frags) for el in et_element.iterfind("OUTPUT-PARAMS/OUTPUT-PARAM")
    ]
    neg_output_params = [
        read_neg_output_param_from_odx(el, doc_frags) for el in et_element.iterfind("NEG-OUTPUT-PARAMS/NEG-OUTPUT-PARAM")
    ]

    # Read boolean flags. Note that the "else" clause contains the default value.
    is_mandatory = True if et_element.get("IS-MANDATORY") == "true" else False
    is_executable = (False if et_element.get("IS-EXECUTABLE") == "false"
                     else True)
    is_final = True if et_element.get("IS-FINAL") == "true" else False

    diag_service = SingleEcuJob(odx_id=odx_id,
                                short_name=short_name,
                                long_name=long_name,
                                description=description,
                                prog_codes=prog_codes,
                                semantic=semantic,
                                audience=audience,
                                functional_class_refs=functional_class_refs,
                                input_params=input_params,
                                output_params=output_params,
                                neg_output_params=neg_output_params,
                                is_mandatory=is_mandatory,
                                is_executable=is_executable,
                                is_final=is_final)
    return diag_service
