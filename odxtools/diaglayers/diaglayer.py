# SPDX-License-Identifier: MIT
from copy import copy, deepcopy
from dataclasses import dataclass
from functools import cached_property
from itertools import chain
from typing import Any, Callable, Dict, Iterable, List, Optional, Union, cast
from xml.etree import ElementTree

from ..admindata import AdminData
from ..companydata import CompanyData
from ..description import Description
from ..diagcomm import DiagComm
from ..diagdatadictionaryspec import DiagDataDictionarySpec
from ..diagservice import DiagService
from ..exceptions import DecodeError, odxassert, odxraise
from ..library import Library
from ..message import Message
from ..nameditemlist import NamedItemList, TNamed
from ..odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from ..parentref import ParentRef
from ..request import Request
from ..response import Response
from ..servicebinner import ServiceBinner
from ..singleecujob import SingleEcuJob
from ..snrefcontext import SnRefContext
from ..specialdatagroup import SpecialDataGroup
from ..subcomponent import SubComponent
from ..unitgroup import UnitGroup
from .diaglayerraw import DiagLayerRaw
from .diaglayertype import DiagLayerType

PrefixTree = Dict[int, Union[List[DiagService], "PrefixTree"]]


@dataclass
class DiagLayer:
    """This class represents a "logical view" upon a diagnostic layer
    according to the ODX standard.

    i.e. it handles the value inheritance, communication parameters,
    encoding/decoding of data, etc.
    """

    diag_layer_raw: DiagLayerRaw

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "DiagLayer":
        diag_layer_raw = DiagLayerRaw.from_et(et_element, doc_frags)

        # Create DiagLayer
        return DiagLayer(diag_layer_raw=diag_layer_raw)

    def __post_init__(self) -> None:
        if self.diag_layer_raw.diag_data_dictionary_spec is None:
            # create an empry DiagDataDictionarySpec object if the raw
            # layer does not define a DDDS...
            self._diag_data_dictionary_spec = DiagDataDictionarySpec(
                admin_data=None,
                data_object_props=NamedItemList(),
                dtc_dops=NamedItemList(),
                structures=NamedItemList(),
                static_fields=NamedItemList(),
                end_of_pdu_fields=NamedItemList(),
                dynamic_endmarker_fields=NamedItemList(),
                dynamic_length_fields=NamedItemList(),
                tables=NamedItemList(),
                env_data_descs=NamedItemList(),
                env_datas=NamedItemList(),
                muxs=NamedItemList(),
                unit_spec=None,
                sdgs=[])
        else:
            self._diag_data_dictionary_spec = self.diag_layer_raw.diag_data_dictionary_spec

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        """Construct a mapping from IDs to all objects that are contained in this diagnostic layer."""
        result = self.diag_layer_raw._build_odxlinks()

        # we want to get the full diag layer, not just the raw layer
        # when referencing...
        result[self.odx_id] = self

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        """Recursively resolve all ODXLINK references."""

        # deal with the import references: these basically extend the
        # pool of objects that are referenceable without having to
        # explicitly specify the DOCREF attribute in the
        # reference. This mechanism can thus be seen as a kind of
        # "poor man's inheritance".
        if self.import_refs:
            imported_links: Dict[OdxLinkId, Any] = {}
            for import_ref in self.import_refs:
                imported_dl = odxlinks.resolve(import_ref, DiagLayer)

                odxassert(
                    imported_dl.variant_type == DiagLayerType.ECU_SHARED_DATA,
                    f"Tried to import references from diagnostic layer "
                    f"'{imported_dl.short_name}' of type {imported_dl.variant_type.value}. "
                    f"Only ECU-SHARED-DATA layers may be referenced using the "
                    f"IMPORT-REF mechanism")

                # TODO: ensure that the imported diagnostic layer has
                # not been referenced in any PARENT-REF of the current
                # layer or any of its parents.

                # TODO: detect and complain about cyclic IMPORT-REFs

                # TODO (?): detect conflicts with locally-defined
                # objects

                imported_dl_links = imported_dl._build_odxlinks()
                for link_id, obj in imported_dl_links.items():
                    # the imported objects shall behave as if they
                    # were defined by the importing layer. IOW, they
                    # must be visible in the same document fragments.
                    link_id = OdxLinkId(link_id.local_id, self.odx_id.doc_fragments)
                    imported_links[link_id] = obj

            # We need to copy the odxlink database here since this
            # function must not modify its argument because the
            # imported references only apply within this specific
            # diagnostic layer
            extended_odxlinks = copy(odxlinks)
            extended_odxlinks.update(imported_links, overwrite=False)

            self.diag_layer_raw._resolve_odxlinks(extended_odxlinks)
            return

        self.diag_layer_raw._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        self.diag_layer_raw._resolve_snrefs(context)

    def _get_local_diag_comms(self, odxlinks: OdxLinkDatabase) -> Iterable[DiagComm]:
        """Return the list of locally defined diagnostic communications.

        This is not completely trivial as it requires to resolving the
        references specified in the <DIAG-COMMS> XML tag.
        """
        return self.diag_layer_raw.diag_comms

    def _get_local_unit_groups(self) -> Iterable[UnitGroup]:
        if self.diag_layer_raw.diag_data_dictionary_spec is None:
            return []

        unit_spec = self.diag_layer_raw.diag_data_dictionary_spec.unit_spec
        if unit_spec is None:
            return []

        return unit_spec.unit_groups

    def _compute_available_objects(
        self,
        get_local_objects: Callable[["DiagLayer"], Iterable[TNamed]],
        get_not_inherited: Callable[[ParentRef], Iterable[str]],
    ) -> Iterable[TNamed]:
        """Helper method to compute the set of all objects applicable
        to the DiagLayer if these objects are subject to the value
        inheritance mechanism

        This is the simplified version for diag layers which do not
        have parents and thus do not deal with value inheritance
        (i.e., ECU-SHARED-DATA).

        """
        return get_local_objects(self)

    def __deepcopy__(self, memo: Dict[int, Any]) -> Any:
        """Create a deep copy of the diagnostic layer

        Note that the copied diagnostic layer is not fully
        initialized, so `_finalize_init()` should to be called on it
        before it can be used normally.
        """
        cls = self.__class__
        result = cls.__new__(cls)
        memo[id(self)] = result

        result.diag_layer_raw = deepcopy(self.diag_layer_raw, memo)

        return result

    #####
    # <convenience functionality>
    #####
    @cached_property
    def service_groups(self) -> ServiceBinner:
        return ServiceBinner(self.services)

    #####
    # </convenience functionality>
    #####

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
    def description(self) -> Optional[Description]:
        return self.diag_layer_raw.description

    @property
    def admin_data(self) -> Optional[AdminData]:
        return self.diag_layer_raw.admin_data

    @property
    def diag_comms(self) -> NamedItemList[DiagComm]:
        return self.diag_layer_raw.diag_comms

    @property
    def services(self) -> NamedItemList[DiagService]:
        return self.diag_layer_raw.services

    @property
    def diag_services(self) -> NamedItemList[DiagService]:
        return self.diag_layer_raw.diag_services

    @property
    def single_ecu_jobs(self) -> NamedItemList[SingleEcuJob]:
        return self.diag_layer_raw.single_ecu_jobs

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
    def global_negative_responses(self) -> NamedItemList[Response]:
        return self.diag_layer_raw.global_negative_responses

    @property
    def import_refs(self) -> List[OdxLinkRef]:
        return self.diag_layer_raw.import_refs

    @property
    def libraries(self) -> NamedItemList[Library]:
        return self.diag_layer_raw.libraries

    @property
    def sub_components(self) -> NamedItemList[SubComponent]:
        return self.diag_layer_raw.sub_components

    @property
    def sdgs(self) -> List[SpecialDataGroup]:
        return self.diag_layer_raw.sdgs

    @property
    def diag_data_dictionary_spec(self) -> DiagDataDictionarySpec:
        """The DiagDataDictionarySpec applicable to this DiagLayer"""
        return self._diag_data_dictionary_spec

    #####
    # </properties forwarded to the "raw" diag layer>
    #####

    #####
    # <PDU decoding>
    #####
    @cached_property
    def _prefix_tree(self) -> PrefixTree:
        """Constructs the coded prefix tree of the services.

        Each leaf node is a list of `DiagService`s.  (This is because
        navigating from a service to the request/ responses is easier
        than finding the service for a given request/response object.)

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
        Note, that the inner `-1` are constant to distinguish them
        from possible service IDs.

        Also note, that it is actually allowed that
        (a) SIDs for different services are the same like for service
            1 and 2 (thus each leaf node is a list) and
        (b) one SID is the prefix of another SID like for service 3
            and 4 (thus the constant `-1` key).

        """
        prefix_tree: PrefixTree = {}
        for s in self.services:
            # Compute prefixes for the service's request and all
            # possible responses. We need to consider the global
            # negative responses here, because they might contain
            # MATCHING-REQUEST parameters. If these global responses
            # do not contain such parameters, this will potentially
            # result in an enormous amount of decoded messages for
            # global negative responses. (I.e., one for each
            # service. This can be avoided by specifying the
            # corresponding request for `decode_response()`.)
            request_prefix = b''
            if s.request is not None:
                request_prefix = s.request.coded_const_prefix()
            prefixes = [request_prefix]
            gnrs = getattr(self, "global_negative_responses", [])
            prefixes += [
                x.coded_const_prefix(request_prefix=request_prefix)
                for x in chain(s.positive_responses, s.negative_responses, gnrs)
            ]
            for coded_prefix in prefixes:
                self._extend_prefix_tree(prefix_tree, coded_prefix, s)

        return prefix_tree

    @staticmethod
    def _extend_prefix_tree(prefix_tree: PrefixTree, coded_prefix: bytes,
                            service: DiagService) -> None:

        # make sure that tree has an entry for the given prefix
        sub_tree = prefix_tree
        for b in coded_prefix:
            if b not in sub_tree:
                sub_tree[b] = {}
            sub_tree = cast(PrefixTree, sub_tree[b])

        # Store the object as in the prefix tree. This is done by
        # assigning the list of possible objects to the key -1 of the
        # dictionary (this is quite hacky...)
        if sub_tree.get(-1) is None:
            sub_tree[-1] = [service]
        else:
            cast(List[DiagService], sub_tree[-1]).append(service)

    def _find_services_for_uds(self, message: bytes) -> List[DiagService]:
        prefix_tree = self._prefix_tree

        # Find matching service(s) in prefix tree
        possible_services: List[DiagService] = []
        for b in message:
            if b in prefix_tree:
                odxassert(isinstance(prefix_tree[b], dict))
                prefix_tree = cast(PrefixTree, prefix_tree[b])
            else:
                break
            if -1 in prefix_tree:
                possible_services += cast(List[DiagService], prefix_tree[-1])
        return possible_services

    def _decode(self, message: bytes, candidate_services: Iterable[DiagService]) -> List[Message]:
        decoded_messages: List[Message] = []

        for service in candidate_services:
            try:
                decoded_messages.append(service.decode_message(message))
            except DecodeError as e:
                # check if the message can be decoded as a global
                # negative response for the service
                gnr_found = False
                for gnr in self.global_negative_responses:
                    try:
                        decoded_gnr = gnr.decode(message)
                        gnr_found = True
                        if not isinstance(decoded_gnr, dict):
                            odxraise(
                                f"Expected the decoded value of a global "
                                f"negative response to be a dictionary, "
                                f"got {type(decoded_gnr)} for {self.short_name}", DecodeError)

                        decoded_messages.append(
                            Message(
                                coded_message=message,
                                service=service,
                                coding_object=gnr,
                                param_dict=decoded_gnr))
                    except DecodeError:
                        pass

                if not gnr_found:
                    raise e

        if len(decoded_messages) == 0:
            raise DecodeError(
                f"None of the services {[x.short_name for x in candidate_services]} could parse {message.hex()}."
            )

        return decoded_messages

    def decode(self, message: bytes) -> List[Message]:
        candidate_services = self._find_services_for_uds(message)

        return self._decode(message, candidate_services)

    def decode_response(self, response: bytes, request: bytes) -> List[Message]:
        candidate_services = self._find_services_for_uds(request)
        if candidate_services is None:
            raise DecodeError(f"Couldn't find corresponding service for request {request.hex()}.")

        return self._decode(response, candidate_services)

    #####
    # </PDU decoding>
    #####
