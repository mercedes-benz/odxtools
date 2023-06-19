# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH
import warnings
from copy import copy
from itertools import chain
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union, cast
from xml.etree import ElementTree

from deprecation import deprecated

from .admindata import AdminData
from .audience import AdditionalAudience, Audience
from .communicationparameter import CommunicationParameterRef
from .companydata import CompanyData, create_company_datas_from_et
from .dataobjectproperty import DopBase, DtcDop
from .diagdatadictionaryspec import DiagDataDictionarySpec
from .diaglayerraw import DiagLayerRaw
from .diaglayertype import DiagLayerType
from .ecu_variant_patterns import EcuVariantPattern, create_ecu_variant_patterns_from_et
from .endofpdufield import EndOfPduField
from .envdata import EnvironmentData
from .envdatadesc import EnvironmentDataDescription
from .exceptions import DecodeError, OdxWarning
from .functionalclass import FunctionalClass
from .globals import logger
from .message import Message
from .multiplexer import Multiplexer
from .nameditemlist import NamedItemList
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .parentref import ParentRef
from .service import DiagService
from .singleecujob import SingleEcuJob
from .specialdata import SpecialDataGroup, create_sdgs_from_et
from .statechart import StateChart
from .structures import BasicStructure, Request, Response, create_any_structure_from_et
from .table import Table
from .units import UnitGroup, UnitSpec
from .utils import create_description_from_et, short_name_as_id


class DiagLayer:
    """This class represents a "logical view" upon a diagnostic layer
    according to the ODX standard.

    i.e. it handles the value inheritance, communication parameters,
    encoding/decoding of data, etc.
    """

    def __init__(self, *, diag_layer_raw: DiagLayerRaw) -> None:
        self.diag_layer_raw = diag_layer_raw

        # diagnostic communications. For convenience, we create
        # separate lists of diag comms for the different kinds of
        # communication objects.
        services = [dc for dc in diag_layer_raw.diag_comms if isinstance(dc, DiagService)]
        single_ecu_jobs = [dc for dc in diag_layer_raw.diag_comms if isinstance(dc, SingleEcuJob)]
        diag_comm_refs = [dc for dc in diag_layer_raw.diag_comms if isinstance(dc, OdxLinkRef)]
        self._local_services = NamedItemList[DiagService](short_name_as_id, services)
        self._local_single_ecu_jobs = NamedItemList[SingleEcuJob](short_name_as_id, single_ecu_jobs)
        self._diag_comm_refs = diag_comm_refs

        # DOP, units, etc
        self.local_diag_data_dictionary_spec = diag_layer_raw.diag_data_dictionary_spec

        # Properties that include inherited objects
        self._services: NamedItemList[Union[DiagService,
                                            SingleEcuJob]] = NamedItemList(short_name_as_id)
        self._data_object_properties: NamedItemList[DopBase] = NamedItemList(short_name_as_id)

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "DiagLayer":
        diag_layer_raw = DiagLayerRaw.from_et(et_element, doc_frags)

        # Create DiagLayer
        return DiagLayer(diag_layer_raw=diag_layer_raw)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        """Construct a mapping from IDs to all objects that are contained in this diagnostic layer."""
        result = self.diag_layer_raw._build_odxlinks()

        # we want to get the full diag layer, not just the raw layer
        # when referencing...
        result[self.odx_id] = self

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        """Recursively resolve all references."""

        self.diag_layer_raw._resolve_odxlinks(odxlinks)

    def _finalize_init(self, odxlinks: OdxLinkDatabase) -> None:
        """This method deals with everything inheritance related and
        -- after the final set of objects covered by the diagnostic
        layer is determined -- resolves any short name references in
        the diagnostic layer.

        TODO: In some corner cases, the short name resolution is not
        correct: E.g. Given three layers A, B, and C, where B and C
        derive from A and A defines the diagnostic communication
        SA. If now B overrides SA and there are short name references
        to SA in A, the object to which this reference is resolved is
        undefined. An easy fix for this problem is to copy all
        inherited objects in derived layers, but that would lead to
        excessive memory consumption for large databases...
        """

        # make sure that the layer which we inherit from are of lower
        # priority than us.
        self_prio = self.variant_type.inheritance_priority
        for parent_ref in self.diag_layer_raw.parent_refs:
            parent_prio = parent_ref.layer.variant_type.inheritance_priority
            assert self_prio > parent_prio, "diagnostic layers can only inherit from layers of lower priority"

        services = sorted(self._compute_available_services(odxlinks), key=short_name_as_id)
        self._services = NamedItemList[Union[DiagService, SingleEcuJob]](short_name_as_id, services)

        dops = NamedItemList[DopBase](short_name_as_id,
                                      self._compute_available_data_object_properties())
        dtc_dops: NamedItemList[DtcDop]
        structures: NamedItemList[BasicStructure]
        end_of_pdu_fields: NamedItemList[EndOfPduField]
        tables: NamedItemList[Table]
        env_data_descs: NamedItemList[EnvironmentDataDescription]
        env_datas: NamedItemList[EnvironmentData]
        muxs: NamedItemList[Multiplexer]
        unit_spec: Optional[UnitSpec]
        ddds_sdgs: List[SpecialDataGroup]
        if self.diag_layer_raw.diag_data_dictionary_spec:
            dtc_dops = self.diag_layer_raw.diag_data_dictionary_spec.dtc_dops
            structures = self.diag_layer_raw.diag_data_dictionary_spec.structures
            end_of_pdu_fields = self.diag_layer_raw.diag_data_dictionary_spec.end_of_pdu_fields
            tables = self.diag_layer_raw.diag_data_dictionary_spec.tables
            env_data_descs = self.diag_layer_raw.diag_data_dictionary_spec.env_data_descs
            env_datas = self.diag_layer_raw.diag_data_dictionary_spec.env_datas
            muxs = self.diag_layer_raw.diag_data_dictionary_spec.muxs
            unit_spec = self.diag_layer_raw.diag_data_dictionary_spec.unit_spec
            ddds_sdgs = self.diag_layer_raw.diag_data_dictionary_spec.sdgs
        else:
            dtc_dops = NamedItemList(short_name_as_id)
            structures = NamedItemList(short_name_as_id)
            end_of_pdu_fields = NamedItemList(short_name_as_id)
            tables = NamedItemList(short_name_as_id)
            env_data_descs = NamedItemList(short_name_as_id)
            env_datas = NamedItemList(short_name_as_id)
            muxs = NamedItemList(short_name_as_id)
            unit_spec = None
            ddds_sdgs = []

        # create a DiagDataDictionarySpec which includes all the
        # inherited objects. To me, this seems rather inelegant, but
        # hey, it's described like this in the standard.
        self._diag_data_dictionary_spec = \
            DiagDataDictionarySpec(
                data_object_props=dops,
                dtc_dops=dtc_dops,
                structures=structures,
                end_of_pdu_fields=end_of_pdu_fields,
                tables=NamedItemList(short_name_as_id, tables),
                env_data_descs=env_data_descs,
                env_datas=env_datas,
                muxs=muxs,
                unit_spec=unit_spec,
                sdgs=ddds_sdgs)

        #####
        # compute the communication parameters applicable to the
        # diagnostic layer
        #####
        self._communication_parameters = self._compute_available_commmunication_parameters()

        self.diag_layer_raw._resolve_snrefs(self)

    #####
    # <properties forwarded to the "raw" diag layer>
    #####
    @property
    def variant_type(self) -> DiagLayerType:
        return self.diag_layer_raw.variant_type

    @property
    def odx_id(self) -> OdxLinkId:
        return self.diag_layer_raw.odx_id

    @property
    def short_name(self) -> str:
        return self.diag_layer_raw.short_name

    @property
    def long_name(self) -> Optional[str]:
        return self.diag_layer_raw.long_name

    @property
    def description(self) -> Optional[str]:
        return self.diag_layer_raw.description

    @property
    def admin_data(self) -> Optional[AdminData]:
        return self.diag_layer_raw.admin_data

    @property
    def company_datas(self) -> NamedItemList[CompanyData]:
        return self.diag_layer_raw.company_datas

    @property
    def requests(self) -> NamedItemList[Request]:
        return self.diag_layer_raw.requests

    @property
    def positive_responses(self) -> NamedItemList[Response]:
        return self.diag_layer_raw.positive_responses

    @property
    def negative_responses(self) -> NamedItemList[Response]:
        return self.diag_layer_raw.negative_responses

    @property
    def import_refs(self) -> List[OdxLinkRef]:
        return self.diag_layer_raw.import_refs

    @property
    def sdgs(self) -> List[SpecialDataGroup]:
        return self.diag_layer_raw.sdgs

    @property
    def parent_refs(self) -> List[ParentRef]:
        return self.diag_layer_raw.parent_refs

    @property
    def ecu_variant_patterns(self) -> List[EcuVariantPattern]:
        return self.diag_layer_raw.ecu_variant_patterns

    #####
    # </properties forwarded to the "raw" diag layer>
    #####

    #######
    # <stuff subject to value inheritance>
    #######

    @property
    def services(self) -> NamedItemList[Union[DiagService, SingleEcuJob]]:
        """All services that this diagnostic layer offers including inherited services."""
        return self._services

    @property
    def diag_data_dictionary_spec(self) -> DiagDataDictionarySpec:
        """The DiagDataDictionarySpec applicable to this DiagLayer"""
        return self._diag_data_dictionary_spec

    #######
    # </stuff subject to value inheritance>
    #######

    #####
    # <value inheritance mechanism helpers>
    #####
    def _get_parent_refs_sorted_by_priority(self, reverse=False):
        return sorted(
            self.diag_layer_raw.parent_refs,
            key=lambda pr: pr.layer.variant_type.inheritance_priority,
            reverse=reverse)

    def __gather_local_services(
            self, odxlinks: OdxLinkDatabase) -> List[Union[DiagService, SingleEcuJob]]:
        diagcomms_by_name: Dict[str, Union[DiagService, SingleEcuJob]] = {}

        for ref in self._diag_comm_refs:
            if (obj := odxlinks.resolve_lenient(ref)) is not None:
                diagcomms_by_name[obj.short_name] = obj
            else:
                logger.warning(f"Diag comm ref {ref!r} could not be resolved.")

        diagcomms_by_name.update({service.short_name: service for service in self._local_services})
        diagcomms_by_name.update({secuj.short_name: secuj for secuj in self._local_single_ecu_jobs})
        return list(diagcomms_by_name.values())

    def _compute_available_services(self, odxlinks: OdxLinkDatabase
                                   ) -> List[Union[DiagService, SingleEcuJob]]:
        """Helper method for initializing the available services.
        This computes the services that are inherited from other diagnostic layers."""
        result_dict = {}

        # Look in parent refs for inherited services Fetch services
        # from low priority parents first, then update with increasing
        # priority
        for parent_ref in self._get_parent_refs_sorted_by_priority():
            for service in parent_ref.get_inherited_services():
                result_dict[service.short_name] = service

        for service in self.__gather_local_services(odxlinks):
            result_dict[service.short_name] = service

        return list(result_dict.values())

    def _compute_available_data_object_properties(self) -> List[DopBase]:
        """Returns the locally defined and inherited DOPs."""
        result_dict = {}

        # Look in parent refs for inherited DOPs. Fetch the DOPs from
        # low priority parents first, then update with increasing
        # priority
        for parent_ref in self._get_parent_refs_sorted_by_priority():
            for dop in parent_ref.get_inherited_data_object_properties():
                result_dict[dop.short_name] = dop

        if self.local_diag_data_dictionary_spec:
            for dop in self.local_diag_data_dictionary_spec.all_data_object_properties:
                result_dict[dop.short_name] = dop

        return list(result_dict.values())

    #####
    # </value inheritance mechanism helpers>
    #####

    #####
    # <communication parameter handling>
    #####
    def _compute_available_commmunication_parameters(self) -> List[CommunicationParameterRef]:
        """Compute the list of communication parameters that apply to
        the diagnostic layer

        Be aware that the inheritance scheme for communication
        parameters is slightly different than for objects that are
        subject to value inheritance:

        - The ODXLINK ID id of communication parameters is used to
          override inherited parameters instead of the short name.
        - A parameter is only overridden if the specified protocol
          matches.

        Note that the specification leaves some room for
        interpretation here: It says that if no protocol is specified,
        the parameter shall apply to any protocol. But what happens if
        the the same comparam is specified with and without a
        protocol? Is this allowed at all? If yes, which of these
        definitions gets priority? How does this interact with
        inheritance? The approach taken here is to allow such cases
        and to use the specific comparams if possible whilst the ones
        without a specified protocol are taken as fallbacks...

        """
        com_params_dict: Dict[Tuple[str, Optional[str]], CommunicationParameterRef] = dict()

        # Look in parent refs for inherited communication
        # parameters. First fetch the communication parameters from
        # low priority parents, then update with increasing priority.
        for parent_ref in self._get_parent_refs_sorted_by_priority():
            for cp in parent_ref.layer._compute_available_commmunication_parameters():
                com_params_dict[(cp.id_ref.ref_id, cp.protocol_snref)] = cp

        # finally, handle the locally defined communication parameters
        for cp in self.diag_layer_raw.communication_parameters:
            com_params_dict[(cp.id_ref.ref_id, cp.protocol_snref)] = cp

        return list(com_params_dict.values())

    @property
    def communication_parameters(self) -> List[CommunicationParameterRef]:
        """All communication parameters applicable to this DiagLayer

        Note that, although communication parameters use inheritance,
        it is *not* the "value inheritance" scheme used by e.g. DOPs,
        tables, state charts, ...
        """
        return self._communication_parameters

    @property
    def protocols(self) -> NamedItemList["DiagLayer"]:
        """Return the set of all protocols which are applicable to the diagnostic layer"""
        result_dict: Dict[str, DiagLayer] = dict()

        for parent_ref in self._get_parent_refs_sorted_by_priority():
            for prot in parent_ref.layer.protocols:
                result_dict[prot.short_name] = prot

        if self.diag_layer_raw.variant_type == DiagLayerType.PROTOCOL:
            result_dict[self.diag_layer_raw.short_name] = self

        return NamedItemList(short_name_as_id, result_dict.values())

    def get_communication_parameter(
        self,
        cp_short_name: str,
        *,
        is_functional: Optional[bool] = None,
        protocol_name: Optional[str] = None,
    ) -> Optional[CommunicationParameterRef]:
        """Find a specific communication parameter according to some criteria.

        Setting a given parameter to `None` means "don't care"."""

        # determine the set of applicable communication parameters
        cps = [cp for cp in self.communication_parameters if cp.short_name == cp_short_name]
        if is_functional is not None:
            cps = [cp for cp in cps if cp.is_functional in (None, is_functional)]
        if protocol_name is not None:
            cps = [cp for cp in cps if cp.protocol_snref in (None, protocol_name)]

        if len(cps) > 1:
            warnings.warn(
                f"Communication parameter `{cp_short_name}` specified more "
                f"than once. Using first occurence.",
                OdxWarning,
            )
        elif len(cps) == 0:
            return None

        return cps[0]

    def get_can_receive_id(self, protocol_name: Optional[str] = None) -> Optional[int]:
        """CAN ID to which the ECU listens for diagnostic messages"""
        com_param = self.get_communication_parameter(
            "CP_UniqueRespIdTable", protocol_name=protocol_name)
        if com_param is None:
            return None

        with warnings.catch_warnings():
            # depending on the protocol, we may get
            # "Communication parameter 'CP_UniqueRespIdTable' does not
            # specify 'CP_CanPhysReqId'" warning here. we don't want this
            # warning and simply return None...
            warnings.simplefilter("ignore", category=OdxWarning)
            result = com_param.get_subvalue("CP_CanPhysReqId")
        if not result:
            return None
        assert isinstance(result, str)

        return int(result)

    @deprecated(details="use get_can_receive_id()")
    def get_receive_id(self) -> Optional[int]:
        return self.get_can_receive_id()

    def get_can_send_id(self, protocol_name: Optional[str] = None) -> Optional[int]:
        """CAN ID to which the ECU sends replies to diagnostic messages"""

        # this hopefully resolves to the 'CP_UniqueRespIdTable'
        # parameter from the ISO_15765_2 comparam subset. (There is a
        # parameter with the same name in the ISO_13400_2_DIS_2015
        # subset for DoIP. If the wrong one is retrieved, try
        # specifying the protocol_name.)
        com_param = self.get_communication_parameter(
            "CP_UniqueRespIdTable", protocol_name=protocol_name)
        if com_param is None:
            return None

        with warnings.catch_warnings():
            # depending on the protocol, we may get
            # "Communication parameter 'CP_UniqueRespIdTable' does not
            # specify 'CP_CanRespUSDTId'" warning here. we don't want this
            # warning and simply return None...
            warnings.simplefilter("ignore", category=OdxWarning)
            result = com_param.get_subvalue("CP_CanRespUSDTId")
        if not result:
            return None
        assert isinstance(result, str)

        return int(result)

    @deprecated(details="use get_can_send_id()")
    def get_send_id(self) -> Optional[int]:
        return self.get_can_send_id()

    def get_can_func_req_id(self, protocol_name: Optional[str] = None) -> Optional[int]:
        """CAN Functional Request Id."""
        com_param = self.get_communication_parameter("CP_CanFuncReqId", protocol_name=protocol_name)
        if com_param is None:
            return None

        result = com_param.get_value()
        if not result:
            return None
        assert isinstance(result, str)

        return int(result)

    def get_doip_logical_ecu_address(self, protocol_name: Optional[str] = None) -> Optional[int]:
        """Return the address of the ECU when using functional addressing.

        The parameter protocol_name is used to distinguish between
        different interfaces, e.g., offboard and onboard DoIP
        Ethernet.
        """

        # this hopefully resolves to the 'CP_UniqueRespIdTable'
        # parameter from the ISO_13400_2_DIS_2015 comparam
        # subset. (There is a parameter with the same name in the
        # ISO_15765_2 subset for CAN. If the wrong one is retrieved,
        # try specifying the protocol_name.)
        com_param = self.get_communication_parameter(
            "CP_UniqueRespIdTable", protocol_name=protocol_name, is_functional=False)

        if com_param is None:
            return None

        # The CP_DoIPLogicalEcuAddress is specified by the
        # "CP_DoIPLogicalEcuAddress" subvalue of the complex Comparam
        # CP_UniqueRespIdTable of the ISO_13400_2_DIS_2015 comparam
        # subset. Depending of the underlying transport protocol,
        # (i.e., CAN using ISO-TP) this subvalue might not exist.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=OdxWarning)
            ecu_addr = com_param.get_subvalue("CP_DoIPLogicalEcuAddress")
        if ecu_addr is None:
            return None
        return int(ecu_addr)

    def get_doip_logical_gateway_address(self,
                                         protocol_name: Optional[str] = None,
                                         is_functional: Optional[bool] = False) -> Optional[int]:
        """The logical gateway address for the diagnosis over IP transport protocol"""

        # retrieve CP_DoIPLogicalGatewayAddress from the
        # ISO_13400_2_DIS_2015 subset. hopefully.
        com_param = self.get_communication_parameter(
            "CP_DoIPLogicalGatewayAddress",
            is_functional=is_functional,
            protocol_name=protocol_name)
        if com_param is None:
            return None

        result = com_param.get_value()
        if not result:
            return None
        assert isinstance(result, str)

        return int(result)

    def get_doip_logical_tester_address(self,
                                        protocol_name: Optional[str] = None,
                                        is_functional: Optional[bool] = False) -> Optional[int]:
        """DoIp logical gateway address"""

        # retrieve CP_DoIPLogicalTesterAddress from the
        # ISO_13400_2_DIS_2015 subset. hopefully.
        com_param = self.get_communication_parameter(
            "CP_DoIPLogicalTesterAddress", is_functional=is_functional, protocol_name=protocol_name)
        if com_param is None:
            return None

        result = com_param.get_value()
        if not result:
            return None
        assert isinstance(result, str)

        return int(result)

    def get_doip_logical_functional_address(self,
                                            protocol_name: Optional[str] = None,
                                            is_functional: Optional[bool] = False) -> Optional[int]:
        """The logical functional DoIP address of the ECU."""

        # retrieve CP_DoIPLogicalFunctionalAddress from the
        # ISO_13400_2_DIS_2015 subset. hopefully.
        com_param = self.get_communication_parameter(
            "CP_DoIPLogicalFunctionalAddress",
            is_functional=is_functional,
            protocol_name=protocol_name,
        )
        if com_param is None:
            return None

        result = com_param.get_value()
        if not result:
            return None
        assert isinstance(result, str)

        return int(result)

    def get_doip_routing_activation_timeout(self,
                                            protocol_name: Optional[str] = None) -> Optional[float]:
        """The timout for the DoIP routing activation request in seconds"""

        # retrieve CP_DoIPRoutingActivationTimeout from the
        # ISO_13400_2_DIS_2015 subset. hopefully.
        com_param = self.get_communication_parameter(
            "CP_DoIPRoutingActivationTimeout", protocol_name=protocol_name)
        if com_param is None:
            return None

        result = com_param.get_value()
        if not result:
            return None
        assert isinstance(result, str)

        return float(result) / 1e6

    def get_doip_routing_activation_type(self,
                                         protocol_name: Optional[str] = None) -> Optional[int]:
        """The DoIP routing activation type

        The number returned has the following meaning:

        0          Default
        1          WWH-OBD (worldwide harmonized onboard diagnostic).
        2-0xDF     reserved
        0xE0-0xFF  OEM-specific
        """

        # retrieve CP_DoIPRoutingActivationType from the
        # ISO_13400_2_DIS_2015 subset. hopefully.
        com_param = self.get_communication_parameter(
            "CP_DoIPRoutingActivationType", protocol_name=protocol_name)
        if com_param is None:
            return None

        result = com_param.get_value()
        if not result:
            return None
        assert isinstance(result, str)

        return int(result)

    def get_tester_present_time(self, protocol_name: Optional[str] = None) -> Optional[float]:
        """Timeout on inactivity in seconds.

        This is defined by the communication parameter "CP_TesterPresentTime".
        If the variant does not define this parameter, the default value 3.0 is returned.

        Description of the comparam: "Time between a response and the
        next subsequent tester present message (if no other request is
        sent to this ECU) in case of physically addressed requests."
        """

        # retrieve CP_TesterPresentTime from either the
        # ISO_13400_2_DIS_2015 or the ISO_15765_2 subset.
        com_param = self.get_communication_parameter(
            "CP_TesterPresentTime", protocol_name=protocol_name)
        if com_param is None:
            return None

        result = com_param.get_value()
        if not result:
            return None
        assert isinstance(result, str)

        # the comparam specifies microseconds. convert this to seconds
        return float(result) / 1e6

    #####
    # </communication parameter handling>
    #####

    #####
    # <PDU decoding>
    #####

    def _build_coded_prefix_tree(self):
        """Constructs the coded prefix tree of the services.
        Each leaf node is a list of `DiagService`s.
        (This is because navigating from a service to the request/ responses is easier than finding the service for a given request/response object.)

        Example:
        Let there be four services with corresponding requests:
        * Request 1 has the coded constant prefix `12 34`.
        * Request 2 has the coded constant prefix `12 34`.
        * Request 3 has the coded constant prefix `12 56`.
        * Request 4 has the coded constant prefix `12 56 00`.

        Then, the constructed prefix tree is the dict
        ```
        {0x12: {0x34: {-1: [<Service 1>, <Service 2>]},
                0x56: {-1: [<Service 3>],
                       0x0: {-1: [<Service 4>]}
                       }}}
        ```
        Note, that the inner `-1` are constant to distinguish them from possible service IDs.

        Also note, that it is actually allowed that
        (a) SIDs for different services are the same like for service 1 and 2 (thus each leaf node is a list) and
        (b) one SID is the prefix of another SID like for service 3 and 4 (thus the constant `-1` key).
        """
        services = [s for s in self._services if isinstance(s, DiagService)]
        prefix_tree = {}
        for s in services:
            # Compute prefixes for the request and all responses
            request_prefix = s.request.coded_const_prefix()
            prefixes = [request_prefix] + [
                message.coded_const_prefix(request_prefix=request_prefix)
                for message in chain(s.positive_responses, s.negative_responses)
            ]
            for coded_prefix in prefixes:
                # Traverse prefix tree
                sub_tree = prefix_tree
                for b in coded_prefix:
                    if sub_tree.get(b) is None:
                        sub_tree[b] = {}
                    sub_tree = sub_tree.get(b)

                    assert isinstance(
                        sub_tree,
                        dict), f"{sub_tree} has type {type(sub_tree)}. How did this happen?"
                # Add service as leaf to prefix tree
                if sub_tree.get(-1) is None:
                    sub_tree[-1] = [s]
                else:
                    sub_tree[-1].append(s)
        return prefix_tree

    def _find_services_for_uds(self, message: Union[bytes, bytearray]):
        if not hasattr(self, "_prefix_tree"):
            # Compute the prefix tree the first time this decode function is called.
            self._prefix_tree = self._build_coded_prefix_tree()
        prefix_tree = self._prefix_tree

        # Find matching service(s) in prefix tree
        possible_services = []
        for b in message:
            if prefix_tree.get(b) is not None:
                assert isinstance(prefix_tree.get(b), dict)
                prefix_tree = prefix_tree.get(b)
            else:
                break
            if -1 in prefix_tree:
                possible_services += prefix_tree[-1]
        return possible_services

    def decode(self, message: Union[bytes, bytearray]) -> Iterable[Message]:
        possible_services = self._find_services_for_uds(message)

        if possible_services is None:
            raise DecodeError(f"Couldn't find corresponding service for message {message.hex()}.")

        decoded_messages = []

        for service in possible_services:
            try:
                decoded_messages.append(service.decode_message(message))
            except DecodeError as e:
                pass
        if len(decoded_messages) == 0:
            raise DecodeError(
                f"None of the services {possible_services} could parse {message.hex()}.")
        return decoded_messages

    def decode_response(self, response: Union[bytes, bytearray],
                        request: Union[bytes, bytearray, Message]) -> Iterable[Message]:
        if isinstance(request, Message):
            possible_services = [request.service]
        else:
            if not isinstance(request, (bytes, bytearray)):
                raise TypeError(f"Request parameter must have type "
                                f"Message, bytes or bytearray but was {type(request)}")
            possible_services = self._find_services_for_uds(request)
        if possible_services is None:
            raise DecodeError(f"Couldn't find corresponding service for request {request.hex()}.")

        decoded_messages = []

        for service in possible_services:
            try:
                decoded_messages.append(service.decode_message(response))
            except DecodeError as e:
                pass
        if len(decoded_messages) == 0:
            raise DecodeError(
                f"None of the services {possible_services} could parse {response.hex()}.")
        return decoded_messages

    #####
    # </PDU decoding>
    #####

    def __repr__(self) -> str:
        return f"""DiagLayer(variant_type={self.diag_layer_raw.variant_type.value},
          odx_id={repr(self.diag_layer_raw.odx_id)},
          short_name={repr(self.diag_layer_raw.short_name)})"""

    def __str__(self) -> str:
        return \
            f"DiagLayer('{self.diag_layer_raw.short_name}', " \
            f"type='{self.diag_layer_raw.variant_type.value}')"
