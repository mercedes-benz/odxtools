# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from itertools import chain
from typing import Optional, Any, Dict, Iterable, List, Union

from .exceptions import *
from .globals import logger, xsi
from .state import read_state_from_odx
from .state_transition import read_state_transition_from_odx

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

# Defines priority of overiding objects
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
                     reference,  # : Union[str, DiagLayer],
                     ref_type: str,
                     not_inherited_diag_comms=[],
                     not_inherited_dops=[]):
            """
            Parameters
            ----------
            reference: str | DiagLayer
                the ID (string) or the referenced DiagLayer
            ref_type: str
            not_inherited_diag_comms: List[str]
                short names of not inherited diag comms
            not_inherited_dops: List[str]
                short names of not inherited DOPs
            """
            assert ref_type in ["PROTOCOL-REF", "BASE-VARIANT-REF",
                                "ECU-SHARED-DATA-REF", "FUNCTIONAL-GROUP-REF"]
            if isinstance(reference, str):
                self.id_ref = reference
                self.referenced_diag_layer = None
            else:
                self.id_ref = reference.id
                self.referenced_diag_layer = reference
            self.not_inherited_diag_comms = not_inherited_diag_comms
            self.not_inherited_dops = not_inherited_dops
            self.ref_type = ref_type

        def _resolve_references(self, id_lookup):
            self.referenced_diag_layer = id_lookup.get(self.id_ref)
            if self.referenced_diag_layer is None:
                logger.warning(
                    f"Could not resolve parent ref to {self.id_ref}")

        def get_inheritance_priority(self):
            return PRIORITY_OF_DIAG_LAYER_TYPE[self.referenced_diag_layer.variant_type]

        def get_inherited_services_by_name(self):
            services = {service.short_name: service for service in self.referenced_diag_layer._services
                        if service.short_name not in self.not_inherited_diag_comms}
            return services

        def get_inherited_data_object_properties_by_name(self):
            dops = {dop.short_name: dop for dop in self.referenced_diag_layer._data_object_properties
                    if dop.short_name not in self.not_inherited_dops}
            return dops

        def get_inherited_communication_parameters_by_name(self):
            return {cp.id_ref: cp for cp in self.referenced_diag_layer._communication_parameters}

    def __init__(self,
                 variant_type,
                 id,
                 short_name,
                 long_name=None,
                 description=None,
                 requests: List[Request] = [],
                 positive_responses: List[Response] = [],
                 negative_responses: List[Response] = [],
                 services: List[DiagService] = [],
                 single_ecu_jobs: List[SingleEcuJob] = [],
                 diag_comm_refs: List[str] = [],
                 parent_refs: List[ParentRef] = [],
                 diag_data_dictionary_spec: DiagDataDictionarySpec = None,
                 communication_parameters:
                 List[CommunicationParameterRef] = [],
                 enable_candela_workarounds=True,
                 id_lookup=None,
                 additional_audiences=[],
                 functional_classes=[],
                 states=[],
                 state_transitions=[]
                 ):
        logger.info(f"Initializing variant type {variant_type}")
        self.variant_type = variant_type

        self.id = id
        self.short_name = short_name
        self.long_name = long_name
        self.description = description

        # Requests and Responses
        self.requests = requests
        self.positive_responses = NamedItemList[Response](lambda pr: pr.short_name,
                                                          positive_responses)
        self.negative_responses = NamedItemList[Response](lambda nr: nr.short_name,
                                                          negative_responses)

        # ParentRefs
        self.parent_refs = parent_refs

        # DiagServices (note that they do not include inherited services!)
        self._local_services = NamedItemList[DiagService](lambda ser: ser.short_name,
                                                          services)
        self._local_single_ecu_jobs = NamedItemList[SingleEcuJob](lambda job: job.short_name,
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
            = NamedItemList(lambda s: s.short_name, [])
        self._communication_parameters: NamedItemList[CommunicationParameterRef]\
            = NamedItemList(lambda s: s.id_ref, [])
        self._data_object_properties: NamedItemList[DopBase]\
            = NamedItemList(lambda s: s.short_name, [])

        if id_lookup is not None:
            self.finalize_init(id_lookup)

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

    def finalize_init(self, id_lookup={}):
        """Resolves all references.

        This method should be called whenever the diag layer (or a referenced object) was changed.
        Particularly, this method assumes that all inherited diag layer are correctly initialized,
        i.e., have resolved their references.
        """
        id_lookup.update(self._build_id_lookup())
        self._resolve_references(id_lookup)

    def _build_id_lookup(self):
        """Construct a mapping from IDs to all objects that are contained in this diagnostic layer."""
        logger.info(f"Adding {self.id} to id_lookup.")

        id_lookup = {}
        for obj in chain(self._local_services,
                         self._local_single_ecu_jobs,
                         self.requests,
                         self.positive_responses,
                         self.negative_responses,
                         self.additional_audiences,
                         self.functional_classes,
                         self.states,
                         self.state_transitions):
            id_lookup[obj.id] = obj

        if self.local_diag_data_dictionary_spec:
            id_lookup.update(
                self.local_diag_data_dictionary_spec._build_id_lookup()
            )

        id_lookup[self.id] = self
        return id_lookup

    def _resolve_references(self, id_lookup: Dict[str, Any]) -> None:
        """Recursively resolve all references."""
        # Resolve inheritance
        for pr in self.parent_refs:
            pr._resolve_references(id_lookup)

        services = sorted(self._compute_available_services_by_name(id_lookup).values(),
                          key=lambda service: service.short_name)
        self._services = NamedItemList[Union[DiagService, SingleEcuJob]](
            lambda s: s.short_name,
            services)

        dops = sorted(self._compute_available_data_object_properties_by_name().values(),
                      key=lambda dop: dop.short_name)
        self._data_object_properties = NamedItemList[DopBase](
            lambda dop: dop.short_name,
            dops)

        comparams = sorted(self._compute_available_commmunication_parameters_by_name().values(),
                           key=lambda comparam: comparam.id_ref)
        self._communication_parameters = NamedItemList[CommunicationParameterRef](
            lambda cp: cp._python_name(),
            comparams)

        # Resolve all other references
        for struct in chain(self.requests,
                            self.positive_responses,
                            self.negative_responses):
            struct._resolve_references(self, id_lookup)

        local_diag_comms: Iterable[Union[DiagService, SingleEcuJob]] \
            = (*self._local_services, *self._local_single_ecu_jobs)
        for service in local_diag_comms:
            service._resolve_references(id_lookup)

        if self.local_diag_data_dictionary_spec:
            self.local_diag_data_dictionary_spec._resolve_references(self,
                                                                     id_lookup)

    def __local_services_by_name(self, id_lookup) -> Dict[str, Union[DiagService, SingleEcuJob]]:
        services_by_name: Dict[str, Union[DiagService, SingleEcuJob]] = {}

        for ref in self._diag_comm_refs:
            if ref in id_lookup:
                services_by_name[id_lookup[ref].short_name] = id_lookup[ref]
            else:
                logger.warning(f"Diag comm ref {ref!r} could not be resolved.")

        services_by_name.update({
            service.short_name: service for service in self._local_services
        })
        services_by_name.update({
            service.short_name: service for service in self._local_single_ecu_jobs
        })
        return services_by_name

    def _compute_available_services_by_name(self, id_lookup) -> Dict[str, DiagService]:
        """Helper method for initializing the available services.
        This computes the services that are inherited from other diagnostic layers."""
        services_by_name = {}

        # Look in parent refs for inherited services
        # Fetch services from low priority parents first, then update with increasing priority
        for parent_ref in self._get_parent_refs_sorted_by_priority():
            services_by_name.update(
                parent_ref.get_inherited_services_by_name())

        services_by_name.update(self.__local_services_by_name(id_lookup))
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
            {cp.id_ref: cp for cp in self._local_communication_parameters})
        return com_params_by_name

    def _get_parent_refs_sorted_by_priority(self, reverse=False):
        return sorted(self.parent_refs, key=lambda pr:  pr.get_inheritance_priority(), reverse=reverse)

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
        services = list(filter(lambda s: isinstance(
            s, DiagService), self._services))
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

    def get_receive_id(self):
        """CAN ID to which the ECU listens for diagnostic messages"""
        # TODO (?): When using the dict notation to access comparams,
        #           wouldn't it be prettier to allow the dot in the id?
        com_param = self.communication_parameters["ISO_15765_2__CP_UniqueRespIdTable"]
        if com_param is None:
            return None
        else:
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
                # fragment of the the ASAM MCD2-D standard.
                return int(com_param.value[1])

    def get_send_id(self):
        """CAN ID to which the ECU sends replies to diagnostic messages"""
        com_param = self.communication_parameters["ISO_15765_2__CP_UniqueRespIdTable"]
        if com_param is None:
            return None
        else:
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
                # fragment of the the ASAM MCD2-D standard.
                return int(com_param.value[4])

    def get_tester_present_time(self):
        """Timeout on inactivity in seconds.

        This is defined by the communication parameter "ISO_14230_3.CP_TesterPresentTime".
        If the variant does not define this parameter, the default value 3.0 is returned.

        Description of the comparam: "Time between a response and the next subsequent tester present message
        (if no other request is sent to this ECU) in case of physically addressed requests."
        """
        cps = list(filter(lambda x: x.id_ref == "ISO_14230_3.CP_TesterPresentTime",
                          self.communication_parameters))
        if len(cps):
            assert len(cps) == 1
            idle_timeout = int(cps[0].value) / 1e6
        else:
            idle_timeout = 3.0  # default specified by the standard
        return idle_timeout

    def __repr__(self) -> str:
        return f"""DiagLayer(variant_type={self.variant_type},
          id={repr(self.id)},
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


def read_parent_ref_from_odx(et_element):
    id_ref = et_element.get("ID-REF")

    not_inherited_diag_comms = [el.get("SHORT-NAME")
                                for el in et_element.iterfind("NOT-INHERITED-DIAG-COMMS/NOT-INHERITED-DIAG-COMM/DIAG-COMM-SNREF")]
    not_inherited_dops = [el.get("SHORT-NAME")
                          for el in et_element.iterfind("NOT-INHERITED-DOPS/NOT-INHERITED-DOP/DOP-BASE-SNREF")]
    ref_type = et_element.get(f"{xsi}type")

    return DiagLayer.ParentRef(
        id_ref,
        ref_type=ref_type,
        not_inherited_diag_comms=not_inherited_diag_comms,
        not_inherited_dops=not_inherited_dops
    )


def read_diag_layer_from_odx(et_element, enable_candela_workarounds=True):

    # logger.info(et_element)
    variant_type = et_element.tag

    id = et_element.get("ID")
    short_name = et_element.find("SHORT-NAME").text

    long_name = et_element.find(
        "LONG-NAME").text if et_element.find("LONG-NAME") is not None else None
    description = read_description_from_odx(et_element.find("DESC"))

    logger.info(f"Parsing {variant_type} '{short_name}' ...")

    # Parse DiagServices
    services = [read_diag_service_from_odx(service)
                for service in et_element.iterfind("DIAG-COMMS/DIAG-SERVICE")]
    diag_comm_refs = [service.get("ID-REF")
                      for service in et_element.iterfind("DIAG-COMMS/DIAG-COMM-REF")]
    single_ecu_jobs = [read_single_ecu_job_from_odx(sej)
                       for sej in et_element.iterfind("DIAG-COMMS/SINGLE-ECU-JOB")]

    # Parse ParentRefs
    parent_refs = [read_parent_ref_from_odx(pr_el)
                   for pr_el in et_element.iterfind("PARENT-REFS/PARENT-REF")]

    # Parse communication parameter refs
    com_params = [read_communication_param_ref_from_odx(el)
                  for el in et_element.iterfind("COMPARAM-REFS/COMPARAM-REF")]

    # Parse Requests and Responses
    requests = [read_structure_from_odx(rq)
                for rq in et_element.iterfind("REQUESTS/REQUEST")]
    positive_responses = [read_structure_from_odx(pr)
                          for pr in et_element.iterfind("POS-RESPONSES/POS-RESPONSE")]
    negative_responses = [read_structure_from_odx(nr)
                          for nr in et_element.iterfind("NEG-RESPONSES/NEG-RESPONSE")]

    additional_audiences = [read_additional_audience_from_odx(el)
                            for el in et_element.iterfind("ADDITIONAL-AUDIENCES/ADDITIONAL-AUDIENCE")]

    functional_classes = [
        read_functional_class_from_odx(el) for el in et_element.iterfind("FUNCT-CLASSS/FUNCT-CLASS")]

    states = [
        read_state_from_odx(el) for el in et_element.iterfind("STATE-CHARTS/STATE-CHART/STATES/STATE")]

    state_transitions = [
        read_state_transition_from_odx(el) for el in
        et_element.iterfind("STATE-CHARTS/STATE-CHART/STATE-TRANSITIONS/STATE-TRANSITION")]

    if et_element.find("DIAG-DATA-DICTIONARY-SPEC"):
        diag_data_dictionary_spec = read_diag_data_dictionary_spec_from_odx(
            et_element.find("DIAG-DATA-DICTIONARY-SPEC"))
    else:
        diag_data_dictionary_spec = None

    # TODO: Are UNIT-SPEC and SDGS needed?

    # Create DiagLayer
    dl = DiagLayer(variant_type,
                   id,
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
                   )

    return dl


class DiagLayerContainer:
    def __init__(self,
                 id,
                 short_name,
                 long_name=None,
                 description=None,
                 admin_data: Optional[AdminData] = None,
                 company_datas: Optional[NamedItemList[CompanyData]] = None,
                 ecu_shared_datas=[],
                 protocols=[],
                 functional_groups=[],
                 base_variants=[],
                 ecu_variants=[]
                 ):
        self.id = id
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
            lambda dop: dop.short_name,
            list(chain(self.ecu_shared_datas, self.protocols, self.functional_groups, self.base_variants, self.ecu_variants)))

    def _build_id_lookup(self):
        result = {}
        if self.admin_data is not None:
            result.update(self.admin_data._build_id_lookup())

        if self.company_datas is not None:
            for cd in self.company_datas:
                result.update(cd._build_id_lookup())

        return result

    def _resolve_references(self, id_lookup: Dict[str, Any]) -> None:
        if self.admin_data is not None:
            self.admin_data._resolve_references(id_lookup)

        if self.company_datas is not None:
            for cd in self.company_datas:
                cd._resolve_references(id_lookup)


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
    id = et_element.get("ID")
    short_name = et_element.find("SHORT-NAME").text
    try:
        long_name = et_element.find("LONG-NAME").text
    except:
        long_name = None
    description = read_description_from_odx(et_element.find("DESC"))
    admin_data = read_admin_data_from_odx(et_element.find("ADMIN-DATA"))
    company_datas = read_company_datas_from_odx(et_element.find("COMPANY-DATAS"))
    ecu_shared_datas = [read_diag_layer_from_odx(dl_element, enable_candela_workarounds=enable_candela_workarounds)
                        for dl_element in et_element.iterfind("ECU-SHARED-DATAS/ECU-SHARED-DATA")]
    protocols = [read_diag_layer_from_odx(dl_element, enable_candela_workarounds=enable_candela_workarounds)
                 for dl_element in et_element.iterfind("PROTOCOLS/PROTOCOL")]
    functional_groups = [read_diag_layer_from_odx(dl_element, enable_candela_workarounds=enable_candela_workarounds)
                         for dl_element in et_element.iterfind("FUNCTIONAL-GROUPS/FUNCTIONAL-GROUP")]
    base_variants = [read_diag_layer_from_odx(dl_element, enable_candela_workarounds=enable_candela_workarounds)
                     for dl_element in et_element.iterfind("BASE-VARIANTS/BASE-VARIANT")]
    ecu_variants = [read_diag_layer_from_odx(dl_element, enable_candela_workarounds=enable_candela_workarounds)
                    for dl_element in et_element.iterfind("ECU-VARIANTS/ECU-VARIANT")]

    return DiagLayerContainer(id,
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
