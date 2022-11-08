# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from itertools import chain
from typing import Optional, Any, Dict, Iterable, List, Union
from copy import copy
import warnings

from .utils import short_name_as_id
from .exceptions import DecodeError, OdxWarning
from .globals import logger, xsi
from .state import read_state_from_odx
from .state_transition import read_state_transition_from_odx

from .odxlink import OdxLinkRef, OdxLinkId,OdxLinkDatabase, OdxDocFragment
from .utils import read_description_from_odx
from .nameditemlist import NamedItemList
from .admindata import AdminData, read_admin_data_from_odx
from .companydata import CompanyData, read_company_datas_from_odx
from .communicationparameter import CommunicationParameterRef, read_communication_param_ref_from_odx
from .diagdatadictionaryspec import DiagDataDictionarySpec, read_diag_data_dictionary_spec_from_odx
from .dataobjectproperty import DopBase
from .functionalclass import read_functional_class_from_odx
from .audience import read_additional_audience_from_odx
from .message import Message
from .service import DiagService, read_diag_service_from_odx
from .singleecujob import SingleEcuJob, read_single_ecu_job_from_odx
from .structures import Request, Response, read_structure_from_odx

# Defines priority of overriding objects
PRIORITY_OF_DIAG_LAYER_TYPE = {
    "PROTOCOL": 1,
    "FUNCTIONAL-GROUP": 2,
    "BASE-VARIANT": 3,
    "ECU-VARIANT": 4,
    # Inherited services from ECU Shared Data always override inherited services from other diag layers
    "ECU-SHARED-DATA": 5
}


class DiagLayer:

    class ParentRef:
        def __init__(self,
                     parent : Union[OdxLinkRef, "DiagLayer"],
                     ref_type: str,
                     not_inherited_diag_comms=[],
                     not_inherited_dops=[]):
            """
            Parameters
            ----------
            parent: OdxLinkRef | DiagLayer
                A reference to the or the parent DiagLayer
            ref_type: str
            not_inherited_diag_comms: List[str]
                short names of not inherited diag comms
            not_inherited_dops: List[str]
                short names of not inherited DOPs
            """
            if ref_type not in ["PROTOCOL-REF", "BASE-VARIANT-REF",
                                "ECU-SHARED-DATA-REF", "FUNCTIONAL-GROUP-REF"]:
                warnings.warn(f'Unknown parent ref type {ref_type}', OdxWarning)
            if isinstance(parent, OdxLinkRef):
                self.parent_ref = parent
                self.parent_diag_layer = None
            else:
                assert isinstance(parent, DiagLayer)

                self.parent_ref = OdxLinkRef.from_id(parent.odx_id)
                self.parent_diag_layer = parent
            self.not_inherited_diag_comms = not_inherited_diag_comms
            self.not_inherited_dops = not_inherited_dops
            self.ref_type = ref_type

        def _resolve_references(self, odxlinks: OdxLinkDatabase):
            self.parent_diag_layer = odxlinks.resolve(self.parent_ref)

        def get_inheritance_priority(self):
            return PRIORITY_OF_DIAG_LAYER_TYPE[self.parent_diag_layer.variant_type]

        def get_inherited_services_by_name(self):
            services = {service.short_name: service for service in self.parent_diag_layer._services
                        if service.short_name not in self.not_inherited_diag_comms}
            return services

        def get_inherited_data_object_properties_by_name(self):
            dops = {dop.short_name: dop for dop in self.parent_diag_layer._data_object_properties
                    if dop.short_name not in self.not_inherited_dops}
            return dops

        def get_inherited_communication_parameters_by_name(self):
            return {cp.id_ref.ref_id: cp for cp in self.parent_diag_layer._communication_parameters}

    def __init__(self,
                 variant_type,
                 odx_id,
                 short_name,
                 long_name=None,
                 description=None,
                 requests: List[Request] = [],
                 positive_responses: List[Response] = [],
                 negative_responses: List[Response] = [],
                 services: List[DiagService] = [],
                 single_ecu_jobs: List[SingleEcuJob] = [],
                 diag_comm_refs: List[OdxLinkRef] = [],
                 parent_refs: List[ParentRef] = [],
                 diag_data_dictionary_spec: Optional[DiagDataDictionarySpec] = None,
                 communication_parameters:
                 Iterable[CommunicationParameterRef] = [],
                 enable_candela_workarounds=True,
                 odxlinks=None,
                 additional_audiences=[],
                 functional_classes=[],
                 states=[],
                 state_transitions=[],
                 import_refs=[],
                 ):
        logger.info(f"Initializing variant type {variant_type}")
        self.variant_type = variant_type

        self.odx_id = odx_id
        self.short_name = short_name
        self.long_name = long_name
        self.description = description

        # Requests and Responses
        self.requests = requests
        self.positive_responses = NamedItemList[Response](short_name_as_id,
                                                          positive_responses)
        self.negative_responses = NamedItemList[Response](short_name_as_id,
                                                          negative_responses)

        # ParentRefs
        self.parent_refs = parent_refs

        # DiagServices (note that they do not include inherited services!)
        self._local_services = NamedItemList[DiagService](short_name_as_id,
                                                          services)
        self._local_single_ecu_jobs = NamedItemList[SingleEcuJob](short_name_as_id,
                                                                  single_ecu_jobs)
        self._diag_comm_refs = diag_comm_refs

        # DOP-BASEs
        self.local_diag_data_dictionary_spec = diag_data_dictionary_spec

        # Communication parameters, e.g. CAN-IDs
        self._local_communication_parameters = NamedItemList[CommunicationParameterRef](lambda cp: cp._python_name(),
                                                                                        communication_parameters)

        self.additional_audiences = additional_audiences
        self.functional_classes = functional_classes
        self.states = states
        self.state_transitions = state_transitions

        # Properties that include inherited objects
        self._services: NamedItemList[Union[DiagService, SingleEcuJob]]\
            = NamedItemList(short_name_as_id, [])
        self._communication_parameters: NamedItemList[CommunicationParameterRef]\
            = NamedItemList(lambda cp: cp._python_name(), [])
        self._data_object_properties: NamedItemList[DopBase]\
            = NamedItemList(short_name_as_id, [])

        self.import_refs = import_refs

        if odxlinks is not None:
            self.finalize_init(odxlinks)

        # specify whether enable work arounds for bugs of CANdela studio
        self._enable_candela_workarounds = enable_candela_workarounds

    @property
    def services(self) -> NamedItemList[Union[DiagService, SingleEcuJob]]:
        """All services that this diagnostic layer offers including inherited services."""
        return self._services

    @property
    def data_object_properties(self) -> NamedItemList[DopBase]:
        """All data object properties including inherited ones.
        This attribute corresponds to all specializations of DOP-BASE
        defined in the DIAG-DATA-DICTIONARY-SPEC of this diag layer as well as
        in the DIAG-DATA-DICTIONARY-SPEC of any parent.
        """
        return self._data_object_properties

    @property
    def communication_parameters(self) -> NamedItemList[CommunicationParameterRef]:
        """All communication parameters including inherited ones."""
        return self._communication_parameters

    def finalize_init(self, odxlinks: Optional[OdxLinkDatabase] = None):
        """Resolves all references.

        This method should be called whenever the diag layer (or a referenced object) was changed.
        Particularly, this method assumes that all inherited diag layer are correctly initialized,
        i.e., have resolved their references.
        """

        if odxlinks is None:
            odxlinks = OdxLinkDatabase()

        odxlinks.update(self._build_odxlinks())
        self._resolve_references(odxlinks)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        """Construct a mapping from IDs to all objects that are contained in this diagnostic layer."""
        logger.info(f"Adding {self.odx_id} to odxlinks.")

        odxlinks = {}

        for obj in chain(self._local_services,
                         self._local_single_ecu_jobs,
                         self.requests,
                         self.positive_responses,
                         self.negative_responses,
                         self.additional_audiences,
                         self.functional_classes,
                         self.states,
                         self.state_transitions):
            odxlinks[obj.odx_id] = obj

        if self.local_diag_data_dictionary_spec:
            odxlinks.update(
                self.local_diag_data_dictionary_spec._build_odxlinks()
            )

        odxlinks[self.odx_id] = self
        return odxlinks

    def _resolve_references(self, odxlinks: OdxLinkDatabase) -> None:
        """Recursively resolve all references."""
        # Resolve inheritance
        for pr in self.parent_refs:
            pr._resolve_references(odxlinks)

        services = sorted(self._compute_available_services_by_name(odxlinks).values(),
                          key=short_name_as_id)
        self._services = NamedItemList[Union[DiagService, SingleEcuJob]](
            short_name_as_id,
            services)

        dops = sorted(self._compute_available_data_object_properties_by_name().values(),
                      key=short_name_as_id)
        self._data_object_properties = NamedItemList[DopBase](
            short_name_as_id,
            dops)

        comparams = sorted(self._compute_available_commmunication_parameters_by_name().values(),
                           key=lambda comparam: comparam.id_ref.ref_id)
        self._communication_parameters = NamedItemList[CommunicationParameterRef](
            lambda cp: cp._python_name(),
            comparams)

        # Resolve all other references
        for struct in chain(self.requests,
                            self.positive_responses,
                            self.negative_responses):
            struct._resolve_references(self, odxlinks)

        local_diag_comms: Iterable[Union[DiagService, SingleEcuJob]] \
            = (*self._local_services, *self._local_single_ecu_jobs)
        for service in local_diag_comms:
            service._resolve_references(odxlinks)

        if self.local_diag_data_dictionary_spec:
            self.local_diag_data_dictionary_spec._resolve_references(self,
                                                                     odxlinks)

    def __local_services_by_name(self, odxlinks: OdxLinkDatabase) -> Dict[str, Union[DiagService, SingleEcuJob]]:
        services_by_name: Dict[str, Union[DiagService, SingleEcuJob]] = {}

        for ref in self._diag_comm_refs:
            if (obj := odxlinks.resolve_lenient(ref)) is not None:
                services_by_name[obj.short_name] = obj
            else:
                logger.warning(f"Diag comm ref {ref!r} could not be resolved.")

        services_by_name.update({
            service.short_name: service for service in self._local_services
        })
        services_by_name.update({
            service.short_name: service for service in self._local_single_ecu_jobs
        })
        return services_by_name

    def _compute_available_services_by_name(self, odxlinks: OdxLinkDatabase) -> Dict[str, DiagService]:
        """Helper method for initializing the available services.
        This computes the services that are inherited from other diagnostic layers."""
        services_by_name = {}

        # Look in parent refs for inherited services
        # Fetch services from low priority parents first, then update with increasing priority
        for parent_ref in self._get_parent_refs_sorted_by_priority():
            services_by_name.update(
                parent_ref.get_inherited_services_by_name())

        services_by_name.update(self.__local_services_by_name(odxlinks))
        return services_by_name

    def _compute_available_data_object_properties_by_name(self) -> Dict[str, DopBase]:
        """Returns the locally defined and inherited DOPs."""
        data_object_properties_by_name = {}

        # Look in parent refs for inherited services
        # Fetch services from low priority parents first, then update with increasing priority
        for parent_ref in self._get_parent_refs_sorted_by_priority():
            data_object_properties_by_name.update(
                parent_ref.get_inherited_data_object_properties_by_name())

        if self.local_diag_data_dictionary_spec:
            data_object_properties_by_name.update({
                d.short_name: d for d in self.local_diag_data_dictionary_spec.all_data_object_properties
            })
        return data_object_properties_by_name

    def _compute_available_commmunication_parameters_by_name(self) -> dict:
        com_params_by_name = {}

        # Look in parent refs for inherited services
        # Fetch services from low priority parents first, then update with increasing priority
        for parent_ref in self._get_parent_refs_sorted_by_priority():
            com_params_by_name.update(
                parent_ref.get_inherited_communication_parameters_by_name())

        com_params_by_name.update(
            {cp.id_ref.ref_id: cp for cp in self._local_communication_parameters})
        return com_params_by_name

    def _get_parent_refs_sorted_by_priority(self, reverse=False):
        return sorted(self.parent_refs, key=lambda pr: pr.get_inheritance_priority(), reverse=reverse)

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
        services = [ s for s in self._services if isinstance(s, DiagService) ]
        prefix_tree = {}
        for s in services:
            # Compute prefixes for the request and all responses
            request_prefix = s.request.coded_const_prefix()
            prefixes = [request_prefix] + [
                message.coded_const_prefix(
                    request_prefix=request_prefix
                ) for message in chain(s.positive_responses, s.negative_responses)
            ]
            for coded_prefix in prefixes:
                # Traverse prefix tree
                sub_tree = prefix_tree
                for b in coded_prefix:
                    if sub_tree.get(b) is None:
                        sub_tree[b] = {}
                    sub_tree = sub_tree.get(b)

                    assert isinstance(
                        sub_tree, dict), f"{sub_tree} has type {type(sub_tree)}. How did this happen?"
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
            raise DecodeError(
                f"Couldn't find corresponding service for message {message.hex()}."
            )

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

    def decode_response(self, response: Union[bytes, bytearray], request: Union[bytes, bytearray, Message]) -> Iterable[Message]:
        if isinstance(request, Message):
            possible_services = [request.service]
        else:
            if not isinstance(request, (bytes, bytearray)):
                raise TypeError(f"Request parameter must have type "
                                f"Message, bytes or bytearray but was {type(request)}")
            possible_services = self._find_services_for_uds(request)
        if possible_services is None:
            raise DecodeError(
                f"Couldn't find corresponding service for request {request.hex()}."
            )

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

    def get_communication_parameter(self, cp_id: str) \
        -> Optional[CommunicationParameterRef]:

        cps = [ cp for cp in self.communication_parameters if cp.id_ref.ref_id == cp_id ]
        if len(cps) > 1:
            warnings.warn(f"Communication parameter `{cp_id}` specified more "
                          f"than once. Using first occurence.", OdxWarning)
        elif len(cps) == 0:
            return None

        return cps[0]

    def get_receive_id(self) -> Optional[int]:
        """CAN ID to which the ECU listens for diagnostic messages"""
        com_param = self.get_communication_parameter("ISO_15765_2.CP_UniqueRespIdTable")

        if com_param is None:
            return None

        if self._enable_candela_workarounds:
            # assume the parameter order used by CANdela studio.
            # note that the parameter ordering actually used
            # differs from the one of the COMPARAM fragment
            # delivered by CANdela generated PDX files and that
            # both are different from the one of the COMPARAM
            # fragment included in the MCD2-D standard
            try:
                return int(com_param.value[2])
            except ValueError:
                return None
        else:
            # assume the parameter order specified by the COMPARAM
            # fragment of the ASAM MCD2-D standard.
            return int(com_param.value[1])

    def get_send_id(self) -> Optional[int]:
        """CAN ID to which the ECU sends replies to diagnostic messages"""
        com_param = self.get_communication_parameter("ISO_15765_2.CP_UniqueRespIdTable")

        if com_param is None:
            return None

        if self._enable_candela_workarounds:
            # assume the parameter order used by CANdela studio.
            # note that the parameter odering actually used
            # differs from the one of the COMPARAM fragment
            # delivered by CANdela generated PDX files and that
            # both are different from the one of the COMPARAM
            # fragment included in the MCD2-D standard
            return int(com_param.value[5])
        else:
            # assume the parameter order specified by the COMPARAM
            # fragment of the ASAM MCD2-D standard.
            return int(com_param.value[4])

    def get_can_func_req_id(self) -> Optional[int]:
        """CAN Functional Request Id."""
        com_param = self.get_communication_parameter("ISO_15765_2.CP_CanFuncReqId")

        if com_param is None:
            return None

        return int(com_param.value)

    def get_logical_doip_address(self) -> Optional[int]:
        """The logical DoIP address of the ECU."""
        com_param = self.get_communication_parameter("ISO_13400_2_DIS_2015.CP_UniqueRespIdTable")

        if com_param is None:
            return None

        return int(com_param.value[0])

    def get_tester_present_time(self) -> Optional[float]:
        """Timeout on inactivity in seconds.

        This is defined by the communication parameter "ISO_15765_3.CP_TesterPresentTime".
        If the variant does not define this parameter, the default value 3.0 is returned.

        Description of the comparam: "Time between a response and the next subsequent tester present message
        (if no other request is sent to this ECU) in case of physically addressed requests."
        """
        com_param = self.get_communication_parameter("ISO_15765_3.CP_TesterPresentTime")

        if com_param is None:
            return 3.0  # default specified by the standard

        return int(com_param.value) / 1e6

    def __repr__(self) -> str:
        return f"""DiagLayer(variant_type={self.variant_type},
          odx_id={repr(self.odx_id)},
          short_name={repr(self.short_name)},
          long_name={repr(self.long_name)},
          description={repr(self.description)},
          requests={self.requests},
          positive_responses={self.positive_responses},
          negative_responses={self.negative_responses},
          services={self._local_services},
          diag_comm_refs={self._diag_comm_refs},
          parent_refs={self.parent_refs},
          diag_data_dictionary_spec={self.local_diag_data_dictionary_spec},
          communication_parameters={self._local_communication_parameters},
          enable_candela_workarounds={self._enable_candela_workarounds})"""

    def __str__(self) -> str:
        return f"DiagLayer('{self.short_name}', type='{self.variant_type}')"


def read_parent_ref_from_odx(et_element, doc_frags: List[OdxDocFragment]) \
    -> DiagLayer.ParentRef:
    parent_ref = OdxLinkRef.from_et(et_element, doc_frags)
    assert parent_ref is not None

    not_inherited_diag_comms = [el.get("SHORT-NAME")
                                for el in et_element.iterfind("NOT-INHERITED-DIAG-COMMS/NOT-INHERITED-DIAG-COMM/DIAG-COMM-SNREF")]
    not_inherited_dops = [el.get("SHORT-NAME")
                          for el in et_element.iterfind("NOT-INHERITED-DOPS/NOT-INHERITED-DOP/DOP-BASE-SNREF")]
    ref_type = et_element.get(f"{xsi}type")

    return DiagLayer.ParentRef(
        parent_ref,
        ref_type=ref_type,
        not_inherited_diag_comms=not_inherited_diag_comms,
        not_inherited_dops=not_inherited_dops
    )


def read_diag_layer_from_odx(et_element,
                             doc_frags: List[OdxDocFragment],
                             enable_candela_workarounds=True) \
    -> DiagLayer:

    variant_type = et_element.tag

    short_name = et_element.find("SHORT-NAME").text
    long_name = et_element.findtext("LONG-NAME")
    description = read_description_from_odx(et_element.find("DESC"))

    logger.info(f"Parsing diagnostic layer '{short_name}' "
                f"of type {variant_type} ...")

    # extend the applicable ODX "document fragments" for the diag layer objects
    doc_frags = copy(doc_frags)
    doc_frags.append(OdxDocFragment(short_name, "LAYER"))

    odx_id = OdxLinkId.from_et(et_element, doc_frags)

    # Parse DiagServices
    services = [read_diag_service_from_odx(service, doc_frags)
                for service in et_element.iterfind("DIAG-COMMS/DIAG-SERVICE")]
    diag_comm_refs = []
    for service in et_element.iterfind("DIAG-COMMS/DIAG-COMM-REF"):
        ref = OdxLinkRef.from_et(service, doc_frags)
        assert ref is not None
        diag_comm_refs.append(ref)

    single_ecu_jobs = [read_single_ecu_job_from_odx(sej, doc_frags)
                       for sej in et_element.iterfind("DIAG-COMMS/SINGLE-ECU-JOB")]

    # Parse ParentRefs
    parent_refs = [read_parent_ref_from_odx(pr_el, doc_frags)
                   for pr_el in et_element.iterfind("PARENT-REFS/PARENT-REF")]

    # Parse communication parameter refs
    com_params = [read_communication_param_ref_from_odx(el, doc_frags)
                  for el in et_element.iterfind("COMPARAM-REFS/COMPARAM-REF")]

    # Parse Requests and Responses
    requests = []
    for rq_elem in et_element.iterfind("REQUESTS/REQUEST"):
        rq = read_structure_from_odx(rq_elem, doc_frags)
        assert isinstance(rq, Request)
        requests.append(rq)

    positive_responses = []
    for pr_elem in et_element.iterfind("POS-RESPONSES/POS-RESPONSE"):
        pr = read_structure_from_odx(pr_elem, doc_frags)
        assert isinstance(pr, Response)
        positive_responses.append(pr)

    negative_responses = []
    for nr_elem in et_element.iterfind("NEG-RESPONSES/NEG-RESPONSE"):
        nr = read_structure_from_odx(nr_elem, doc_frags)
        assert isinstance(nr, Response)
        negative_responses.append(nr)

    additional_audiences = [read_additional_audience_from_odx(el, doc_frags)
                            for el in et_element.iterfind("ADDITIONAL-AUDIENCES/ADDITIONAL-AUDIENCE")]

    functional_classes = [
        read_functional_class_from_odx(el, doc_frags)
        for el in et_element.iterfind("FUNCT-CLASSS/FUNCT-CLASS")]

    states = [
        read_state_from_odx(el, doc_frags)
        for el in et_element.iterfind("STATE-CHARTS/STATE-CHART/STATES/STATE")]

    state_transitions = [
        read_state_transition_from_odx(el, doc_frags)
        for el in et_element.iterfind("STATE-CHARTS/"
                                      "STATE-CHART/"
                                      "STATE-TRANSITIONS/"
                                      "STATE-TRANSITION")]

    if et_element.find("DIAG-DATA-DICTIONARY-SPEC"):
        diag_data_dictionary_spec = read_diag_data_dictionary_spec_from_odx(
            et_element.find("DIAG-DATA-DICTIONARY-SPEC"), doc_frags)
    else:
        diag_data_dictionary_spec = None

    import_refs = [OdxLinkRef.from_et(ref, doc_frags)
                   for ref in et_element.iterfind("IMPORT-REFS/IMPORT-REF")]

    # TODO: Are UNIT-SPEC and SDGS needed?

    # Create DiagLayer
    dl = DiagLayer(variant_type,
                   odx_id,
                   short_name,
                   long_name=long_name,
                   description=description,
                   requests=requests,
                   positive_responses=positive_responses,
                   negative_responses=negative_responses,
                   services=services,
                   diag_comm_refs=diag_comm_refs,
                   single_ecu_jobs=single_ecu_jobs,
                   parent_refs=parent_refs,
                   diag_data_dictionary_spec=diag_data_dictionary_spec,
                   communication_parameters=com_params,
                   additional_audiences=additional_audiences,
                   functional_classes=functional_classes,
                   states=states,
                   state_transitions=state_transitions,
                   enable_candela_workarounds=enable_candela_workarounds,
                   import_refs=import_refs,
                   )

    return dl


class DiagLayerContainer:
    def __init__(self,
                 odx_id: OdxLinkId,
                 short_name: str,
                 long_name: Optional[str] = None,
                 description: Optional[str] = None,
                 admin_data: Optional[AdminData] = None,
                 company_datas: Optional[NamedItemList[CompanyData]] = None,
                 ecu_shared_datas: List[DiagLayer] = [],
                 protocols: List[DiagLayer] = [],
                 functional_groups: List[DiagLayer] = [],
                 base_variants: List[DiagLayer] = [],
                 ecu_variants: List[DiagLayer] = []
                 ) -> None:
        self.odx_id = odx_id
        self.short_name = short_name
        self.long_name = long_name
        self.description = description
        self.admin_data = admin_data
        self.company_datas = company_datas

        self.ecu_shared_datas = ecu_shared_datas
        self.protocols = protocols
        self.functional_groups = functional_groups
        self.base_variants = base_variants
        self.ecu_variants = ecu_variants

        self._diag_layers = NamedItemList[DiagLayer](
            short_name_as_id,
            list(chain(self.ecu_shared_datas, self.protocols, self.functional_groups, self.base_variants, self.ecu_variants)))

    def _build_odxlinks(self):
        result = {}
        result[self.odx_id] = self

        if self.admin_data is not None:
            result.update(self.admin_data._build_odxlinks())

        if self.company_datas is not None:
            for cd in self.company_datas:
                result.update(cd._build_odxlinks())

        return result

    def _resolve_references(self, odxlinks: OdxLinkDatabase) -> None:
        if self.admin_data is not None:
            self.admin_data._resolve_references(odxlinks)

        if self.company_datas is not None:
            for cd in self.company_datas:
                cd._resolve_references(odxlinks)


    @property
    def diag_layers(self):
        return self._diag_layers

    def __getitem__(self, key: Union[int, str]) -> DiagLayer:
        return self.diag_layers[key]

    def __repr__(self) -> str:
        return f"DiagLayerContainer('{self.short_name}')"

    def __str__(self) -> str:
        return f"DiagLayerContainer('{self.short_name}')"


def read_diag_layer_container_from_odx(et_element, enable_candela_workarounds=True):
    short_name = et_element.findtext("SHORT-NAME")
    assert short_name is not None
    long_name = et_element.findtext("LONG-NAME")

    # create the current ODX "document fragment" (description of the
    # current document for references and IDs)
    doc_frags = [ OdxDocFragment(short_name, "CONTAINER") ]

    odx_id = OdxLinkId.from_et(et_element, doc_frags)
    assert odx_id is not None
    description = read_description_from_odx(et_element.find("DESC"))
    admin_data = read_admin_data_from_odx(et_element.find("ADMIN-DATA"), doc_frags)
    company_datas = read_company_datas_from_odx(et_element.find("COMPANY-DATAS"), doc_frags)
    ecu_shared_datas = [read_diag_layer_from_odx(dl_element,
                                                 doc_frags,
                                                 enable_candela_workarounds=enable_candela_workarounds)
                        for dl_element in et_element.iterfind("ECU-SHARED-DATAS/ECU-SHARED-DATA")]
    protocols = [read_diag_layer_from_odx(dl_element,
                                          doc_frags,
                                          enable_candela_workarounds=enable_candela_workarounds)
                 for dl_element in et_element.iterfind("PROTOCOLS/PROTOCOL")]
    functional_groups = [read_diag_layer_from_odx(dl_element,
                                                  doc_frags,
                                                  enable_candela_workarounds=enable_candela_workarounds)
                         for dl_element in et_element.iterfind("FUNCTIONAL-GROUPS/FUNCTIONAL-GROUP")]
    base_variants = [read_diag_layer_from_odx(dl_element,
                                              doc_frags,
                                              enable_candela_workarounds=enable_candela_workarounds)
                     for dl_element in et_element.iterfind("BASE-VARIANTS/BASE-VARIANT")]
    ecu_variants = [read_diag_layer_from_odx(dl_element,
                                             doc_frags,
                                             enable_candela_workarounds=enable_candela_workarounds)
                    for dl_element in et_element.iterfind("ECU-VARIANTS/ECU-VARIANT")]

    return DiagLayerContainer(odx_id,
                              short_name,
                              long_name=long_name,
                              description=description,
                              admin_data=admin_data,
                              company_datas=company_datas,
                              ecu_shared_datas=ecu_shared_datas,
                              protocols=protocols,
                              functional_groups=functional_groups,
                              base_variants=base_variants,
                              ecu_variants=ecu_variants
                              )
