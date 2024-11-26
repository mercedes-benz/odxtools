# SPDX-License-Identifier: MIT
import re
import warnings
from copy import deepcopy
from dataclasses import dataclass
from functools import cached_property
from typing import (TYPE_CHECKING, Any, Callable, Dict, Iterable, List, Optional, Tuple, TypeVar,
                    Union, cast)
from xml.etree import ElementTree

from ..additionalaudience import AdditionalAudience
from ..admindata import AdminData
from ..comparaminstance import ComparamInstance
from ..diagcomm import DiagComm
from ..diagdatadictionaryspec import DiagDataDictionarySpec
from ..diagservice import DiagService
from ..exceptions import OdxWarning, odxassert, odxraise
from ..functionalclass import FunctionalClass
from ..nameditemlist import NamedItemList, OdxNamed
from ..odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from ..parentref import ParentRef
from ..response import Response
from ..singleecujob import SingleEcuJob
from ..snrefcontext import SnRefContext
from ..specialdatagroup import SpecialDataGroup
from ..statechart import StateChart
from ..unitgroup import UnitGroup
from ..unitspec import UnitSpec
from .diaglayer import DiagLayer
from .hierarchyelementraw import HierarchyElementRaw

if TYPE_CHECKING:
    from .database import Database
    from .protocol import Protocol

TNamed = TypeVar("TNamed", bound=OdxNamed)


@dataclass
class HierarchyElement(DiagLayer):
    """This is the base class for diagnostic layers that may be involved in value inheritance
    """

    @property
    def hierarchy_element_raw(self) -> HierarchyElementRaw:
        return cast(HierarchyElementRaw, self.diag_layer_raw)

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "HierarchyElement":
        hierarchy_element_raw = HierarchyElementRaw.from_et(et_element, doc_frags)

        return HierarchyElement(diag_layer_raw=hierarchy_element_raw)

    def __post_init__(self) -> None:
        super().__post_init__()

        self._global_negative_responses: NamedItemList[Response]

        odxassert(
            isinstance(self.diag_layer_raw, HierarchyElementRaw),
            "The raw diagnostic layer passed to HierarchyElement "
            "must be a HierarchyElementRaw")

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result = super()._build_odxlinks()

        return result

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        super()._resolve_odxlinks(odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

    def __deepcopy__(self, memo: Dict[int, Any]) -> Any:
        """Create a deep copy of the hierarchy element

        Note that the copied diagnostic layer is not fully
        initialized, so `_finalize_init()` should to be called on it
        before it can be used normally.
        """

        new_he = super().__deepcopy__(memo)

        # note that the self.hierarchy_element_raw object is *not*
        # copied at this place because the attribute points to the
        # same object as self.diag_layer_raw.
        new_he.hierarchy_element_raw = deepcopy(self.hierarchy_element_raw)

        return new_he

    def _finalize_init(self, database: "Database", odxlinks: OdxLinkDatabase) -> None:
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

        #####
        # fill in all applicable objects that use value inheritance
        #####

        self._compute_value_inheritance(odxlinks)

        ############
        # create a new unit_spec object. This is necessary because
        # unit_groups are subject to value inheritance.

        # unit groups applicable to this diaglayer (i.e., including
        # value inheritance)
        unit_groups = self._compute_available_unit_groups()

        # convenience variable for the locally-defined unit spec
        local_unit_spec: Optional[UnitSpec]
        if self.diag_layer_raw.diag_data_dictionary_spec is not None:
            local_unit_spec = self.diag_layer_raw.diag_data_dictionary_spec.unit_spec
        else:
            local_unit_spec = None

        unit_spec: Optional[UnitSpec]
        if local_unit_spec is None and not unit_groups:
            # no locally defined unit spec and no inherited unit groups
            unit_spec = None
        elif local_unit_spec is None:
            # no locally defined unit spec but inherited unit groups
            unit_spec = UnitSpec(
                unit_groups=NamedItemList(unit_groups),
                units=NamedItemList([]),
                physical_dimensions=NamedItemList([]),
                sdgs=[])
        else:
            # locally defined unit spec and inherited unit groups
            unit_spec = UnitSpec(
                unit_groups=NamedItemList(unit_groups),
                units=local_unit_spec.units,
                physical_dimensions=local_unit_spec.physical_dimensions,
                sdgs=[])
        ############

        dops = self._compute_available_ddd_spec_items(
            lambda ddd_spec: ddd_spec.data_object_props,
            lambda parent_ref: parent_ref.not_inherited_dops,
        )
        structures = self._compute_available_ddd_spec_items(
            lambda ddd_spec: ddd_spec.structures,
            lambda parent_ref: parent_ref.not_inherited_dops,
        )
        dtc_dops = self._compute_available_ddd_spec_items(
            lambda ddd_spec: ddd_spec.dtc_dops,
            lambda parent_ref: parent_ref.not_inherited_dops,
        )
        static_fields = self._compute_available_ddd_spec_items(
            lambda ddd_spec: ddd_spec.static_fields,
            lambda parent_ref: parent_ref.not_inherited_dops,
        )
        end_of_pdu_fields = self._compute_available_ddd_spec_items(
            lambda ddd_spec: ddd_spec.end_of_pdu_fields,
            lambda parent_ref: parent_ref.not_inherited_dops,
        )
        dynamic_endmarker_fields = self._compute_available_ddd_spec_items(
            lambda ddd_spec: ddd_spec.dynamic_endmarker_fields,
            lambda parent_ref: parent_ref.not_inherited_dops,
        )
        dynamic_length_fields = self._compute_available_ddd_spec_items(
            lambda ddd_spec: ddd_spec.dynamic_length_fields,
            lambda parent_ref: parent_ref.not_inherited_dops,
        )
        env_data_descs = self._compute_available_ddd_spec_items(
            lambda ddd_spec: ddd_spec.env_data_descs,
            lambda parent_ref: parent_ref.not_inherited_dops,
        )
        env_datas = self._compute_available_ddd_spec_items(
            lambda ddd_spec: ddd_spec.env_datas, lambda parent_ref: parent_ref.not_inherited_dops)
        muxs = self._compute_available_ddd_spec_items(
            lambda ddd_spec: ddd_spec.muxs, lambda parent_ref: parent_ref.not_inherited_dops)
        tables = self._compute_available_ddd_spec_items(
            lambda ddd_spec: ddd_spec.tables, lambda parent_ref: parent_ref.not_inherited_tables)

        ddds_admin_data: Optional[AdminData] = None
        ddds_sdgs: List[SpecialDataGroup] = []
        if self.diag_layer_raw.diag_data_dictionary_spec:
            ddds_admin_data = self.diag_layer_raw.diag_data_dictionary_spec.admin_data
            ddds_sdgs = self.diag_layer_raw.diag_data_dictionary_spec.sdgs

        # create a DiagDataDictionarySpec which includes all the
        # inherited objects. To me, this seems rather inelegant, but
        # hey, it's described like this in the standard.
        self._diag_data_dictionary_spec = DiagDataDictionarySpec(
            admin_data=ddds_admin_data,
            data_object_props=dops,
            dtc_dops=dtc_dops,
            structures=structures,
            static_fields=static_fields,
            end_of_pdu_fields=end_of_pdu_fields,
            dynamic_endmarker_fields=dynamic_endmarker_fields,
            dynamic_length_fields=dynamic_length_fields,
            tables=tables,
            env_data_descs=env_data_descs,
            env_datas=env_datas,
            muxs=muxs,
            unit_spec=unit_spec,
            sdgs=ddds_sdgs,
        )

        #####
        # compute the communication parameters applicable to the
        # diagnostic layer. Note that communication parameters do
        # *not* use value inheritance, but a slightly different
        # scheme, cf the docstring of
        # _compute_available_commmunication_parameters().
        #####
        self._comparam_refs = NamedItemList(self._compute_available_commmunication_parameters())

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

    #####
    # <value inheritance mechanism helpers>
    #####
    def _compute_value_inheritance(self, odxlinks: OdxLinkDatabase) -> None:
        # diagnostic communication objects with the ODXLINKs resolved
        diag_comms = self._compute_available_diag_comms(odxlinks)
        self._diag_comms = NamedItemList[DiagComm](diag_comms)

        # filter the diag comms for services and single-ECU jobs
        diag_services = [dc for dc in diag_comms if isinstance(dc, DiagService)]
        single_ecu_jobs = [dc for dc in diag_comms if isinstance(dc, SingleEcuJob)]
        self._diag_services = NamedItemList(diag_services)
        self._single_ecu_jobs = NamedItemList(single_ecu_jobs)

        global_negative_responses = self._compute_available_global_neg_responses(odxlinks)
        self._global_negative_responses = NamedItemList(global_negative_responses)

        functional_classes = self._compute_available_functional_classes()
        self._functional_classes = NamedItemList(functional_classes)

        additional_audiences = self._compute_available_additional_audiences()
        self._additional_audiences = NamedItemList(additional_audiences)

        state_charts = self._compute_available_state_charts()
        self._state_charts = NamedItemList(state_charts)

    def _get_parent_refs_sorted_by_priority(self, reverse: bool = False) -> Iterable[ParentRef]:
        return sorted(
            getattr(self.diag_layer_raw, "parent_refs", []),
            key=lambda pr: pr.layer.variant_type.inheritance_priority,
            reverse=reverse)

    def _compute_available_objects(
        self,
        get_local_objects: Callable[["DiagLayer"], Iterable[TNamed]],
        get_not_inherited: Callable[[ParentRef], Iterable[str]],
    ) -> Iterable[TNamed]:
        """Helper method to compute the set of all objects applicable
        to the DiagLayer if these objects are subject to the value
        inheritance mechanism

        Note that all objects subject to the value inheritance
        mechanism exhibit a short_name attribute.

        :param get_local_objects: Function mapping a DiagLayer to the
        set of objects that are locally defined by that DiagLayer. If
        any of these objects have already been defined in any of the
        parents, the locally defined instance overrides them.

        :param get_not_inherited: Function mapping a ParentRef to the
        set of short names of the objects which shall not be inherited
        from the parents.

        """

        local_objects = get_local_objects(self)
        local_object_short_names = {x.short_name for x in local_objects}
        result_dict: Dict[str, Tuple[TNamed, DiagLayer]] = {}

        # populate the result dictionary with the inherited objects
        for parent_ref in self._get_parent_refs_sorted_by_priority(reverse=True):
            parent_dl = parent_ref.layer

            # retrieve the set of short names of the objects which we
            # are not supposed to inherit
            not_inherited_short_names = set(get_not_inherited(parent_ref))

            # compute the list of objects which we are supposed to
            # inherit from this diagnostic layer
            inherited_objects = [
                x
                for x in parent_dl._compute_available_objects(get_local_objects, get_not_inherited)
                if x.short_name not in not_inherited_short_names
            ]

            # update the result set with the objects from the current parent_ref
            for obj in inherited_objects:

                # no object with the given short name currently
                # exits. add it to the result set and continue
                if obj.short_name not in result_dict:
                    result_dict[obj.short_name] = (obj, parent_dl)
                    continue

                # if an object with a given name already exists,
                # there's no problem if it was inherited from a parent
                # of different priority than the one currently
                # considered
                orig_prio = result_dict[obj.short_name][1].variant_type.inheritance_priority
                new_prio = parent_dl.variant_type.inheritance_priority
                if new_prio < orig_prio:
                    continue
                elif orig_prio < new_prio:
                    result_dict[obj.short_name] = (obj, parent_dl)
                    continue

                # if there is a conflict on the same priority level,
                # it does not matter if the object is overridden
                # locally anyway...
                if obj.short_name in local_object_short_names:
                    continue

                # if all of these conditions do not apply, and if the
                # inherited objects are identical, there is no
                # conflict. (note that value comparisons of complete
                # complex objects tend to be expensive, so this test
                # is done last.)
                if obj == result_dict[obj.short_name][0]:
                    continue

                odxraise(f"Diagnostic layer {self.short_name} cannot inherit object "
                         f"{obj.short_name} due to an unresolveable inheritance conflict between "
                         f"parent layers {result_dict[obj.short_name][1].short_name} "
                         f"and {parent_dl.short_name}")

        # add the locally defined entries, overriding the inherited
        # ones if necessary
        for obj in local_objects:
            result_dict[obj.short_name] = (obj, self)

        return [x[0] for x in result_dict.values()]

    def _compute_available_diag_comms(self, odxlinks: OdxLinkDatabase) -> Iterable[DiagComm]:

        def get_local_objects_fn(dl: DiagLayer) -> Iterable[DiagComm]:
            return dl._get_local_diag_comms(odxlinks)

        def not_inherited_fn(parent_ref: ParentRef) -> List[str]:
            return parent_ref.not_inherited_diag_comms

        return self._compute_available_objects(get_local_objects_fn, not_inherited_fn)

    def _compute_available_global_neg_responses(self, odxlinks: OdxLinkDatabase) \
            -> Iterable[Response]:

        def get_local_objects_fn(dl: DiagLayer) -> Iterable[Response]:
            return dl.diag_layer_raw.global_negative_responses

        def not_inherited_fn(parent_ref: ParentRef) -> List[str]:
            return parent_ref.not_inherited_global_neg_responses

        return self._compute_available_objects(get_local_objects_fn, not_inherited_fn)

    def _compute_available_ddd_spec_items(
        self,
        include: Callable[[DiagDataDictionarySpec], Iterable[TNamed]],
        exclude: Callable[["ParentRef"], List[str]],
    ) -> NamedItemList[TNamed]:

        def get_local_objects_fn(dl: DiagLayer) -> Iterable[TNamed]:
            if dl.diag_layer_raw.diag_data_dictionary_spec is None:
                return []
            return include(dl.diag_layer_raw.diag_data_dictionary_spec)

        found = self._compute_available_objects(get_local_objects_fn, exclude)
        return NamedItemList(found)

    def _compute_available_functional_classes(self) -> Iterable[FunctionalClass]:

        def get_local_objects_fn(dl: DiagLayer) -> Iterable[FunctionalClass]:
            return dl.diag_layer_raw.functional_classes

        def not_inherited_fn(parent_ref: ParentRef) -> List[str]:
            return []

        return self._compute_available_objects(get_local_objects_fn, not_inherited_fn)

    def _compute_available_additional_audiences(self) -> Iterable[AdditionalAudience]:

        def get_local_objects_fn(dl: DiagLayer) -> Iterable[AdditionalAudience]:
            return dl.diag_layer_raw.additional_audiences

        def not_inherited_fn(parent_ref: ParentRef) -> List[str]:
            return []

        return self._compute_available_objects(get_local_objects_fn, not_inherited_fn)

    def _compute_available_state_charts(self) -> Iterable[StateChart]:

        def get_local_objects_fn(dl: DiagLayer) -> Iterable[StateChart]:
            return dl.diag_layer_raw.state_charts

        def not_inherited_fn(parent_ref: ParentRef) -> List[str]:
            return []

        return self._compute_available_objects(get_local_objects_fn, not_inherited_fn)

    def _compute_available_unit_groups(self) -> Iterable[UnitGroup]:

        def get_local_objects_fn(dl: DiagLayer) -> Iterable[UnitGroup]:
            return dl._get_local_unit_groups()

        def not_inherited_fn(parent_ref: ParentRef) -> List[str]:
            return []

        return self._compute_available_objects(get_local_objects_fn, not_inherited_fn)

    #####
    # </value inheritance mechanism helpers>
    #####

    #######
    # <properties subject to value inheritance>
    #######
    @property
    def diag_data_dictionary_spec(self) -> DiagDataDictionarySpec:
        return self._diag_data_dictionary_spec

    @property
    def diag_comms(self) -> NamedItemList[DiagComm]:
        """All diagnostic communication primitives applicable to this DiagLayer

        Diagnostic communication primitives are diagnostic services as
        well as single-ECU jobs. This list has all references
        resolved.
        """
        return self._diag_comms

    @property
    def services(self) -> NamedItemList[DiagService]:
        """This property is an alias for `.diag_services`"""
        return self._diag_services

    @property
    def diag_services(self) -> NamedItemList[DiagService]:
        """All diagnostic services applicable to this DiagLayer

        This is a subset of all diagnostic communication
        primitives. All references are resolved in the list returned.
        """
        return self._diag_services

    @property
    def single_ecu_jobs(self) -> NamedItemList[SingleEcuJob]:
        """All single-ECU jobs applicable to this DiagLayer

        This is a subset of all diagnostic communication
        primitives. All references are resolved in the list returned.
        """
        return self._single_ecu_jobs

    @property
    def global_negative_responses(self) -> NamedItemList[Response]:
        """All global negative responses applicable to this DiagLayer"""
        return self._global_negative_responses

    @property
    def functional_classes(self) -> NamedItemList[FunctionalClass]:
        """All functional classes applicable to this DiagLayer"""
        return self._functional_classes

    @property
    def state_charts(self) -> NamedItemList[StateChart]:
        """All state charts applicable to this DiagLayer"""
        return self._state_charts

    @property
    def additional_audiences(self) -> NamedItemList[AdditionalAudience]:
        """All audiences applicable to this DiagLayer"""
        return self._additional_audiences

    #######
    # </properties subject to value inheritance>
    #######

    #####
    # <communication parameter handling>
    #####
    def _compute_available_commmunication_parameters(self) -> List[ComparamInstance]:
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
        com_params_dict: Dict[Tuple[str, Optional[str]], ComparamInstance] = {}

        # Look in parent refs for inherited communication
        # parameters. First fetch the communication parameters from
        # low priority parents, then update with increasing priority.
        for parent_ref in self._get_parent_refs_sorted_by_priority():
            parent_layer = parent_ref.layer
            if not isinstance(parent_layer, HierarchyElement):
                continue
            for cp in parent_layer._compute_available_commmunication_parameters():
                com_params_dict[(cp.spec_ref.ref_id, cp.protocol_snref)] = cp

        # finally, handle the locally defined communication parameters
        for cp in getattr(self.hierarchy_element_raw, "comparam_refs", []):
            com_params_dict[(cp.spec_ref.ref_id, cp.protocol_snref)] = cp

        return list(com_params_dict.values())

    @property
    def comparam_refs(self) -> NamedItemList[ComparamInstance]:
        """All communication parameters applicable to this DiagLayer

        Note that, although communication parameters use inheritance,
        it is *not* the "value inheritance" scheme used by e.g. DOPs,
        tables, state charts, ...
        """
        return self._comparam_refs

    @cached_property
    def protocols(self) -> NamedItemList["Protocol"]:
        """Return the set of all protocols which are applicable to the diagnostic layer

        Note that protocols are *not* explicitly defined by the XML,
        but they are the parent layers of variant type "PROTOCOL".

        """
        from .protocol import Protocol

        result_dict: Dict[str, Protocol] = {}

        for parent_ref in getattr(self, "parent_refs", []):
            for prot in getattr(parent_ref.layer, "protocols", []):
                result_dict[prot.short_name] = prot

        if isinstance(self, Protocol):
            result_dict[self.diag_layer_raw.short_name] = self

        return NamedItemList(result_dict.values())

    def get_comparam(
        self,
        cp_short_name: str,
        *,
        protocol: Optional[Union[str, "Protocol"]] = None,
    ) -> Optional[ComparamInstance]:
        """Find a specific communication parameter according to some criteria.

        Setting a given parameter to `None` means "don't care"."""

        from .protocol import Protocol

        protocol_name: Optional[str]
        if isinstance(protocol, Protocol):
            protocol_name = protocol.short_name
        else:
            protocol_name = protocol

        # determine the set of applicable communication parameters
        cps = [cp for cp in self.comparam_refs if cp.short_name == cp_short_name]
        if protocol_name is not None:
            cps = [cp for cp in cps if cp.protocol_snref in (None, protocol_name)]

        if len(cps) > 1:
            warnings.warn(
                f"Communication parameter `{cp_short_name}` specified more "
                f"than once. Using first occurence.",
                OdxWarning,
                stacklevel=1,
            )
        elif len(cps) == 0:
            return None

        return cps[0]

    def get_max_can_payload_size(self,
                                 protocol: Optional[Union[str,
                                                          "Protocol"]] = None) -> Optional[int]:
        """Return the maximum size of a CAN frame payload that can be
        transmitted in bytes.

        For classic CAN busses, this is basically always 8. CAN-FD can
        send up to 64 bytes per frame.

        """
        com_param = self.get_comparam("CP_CANFDTxMaxDataLength", protocol=protocol)
        if com_param is None:
            rx_id = self.get_can_receive_id(protocol=protocol)
            if rx_id is not None:
                # bus is CAN. We also use 8 bytes for CAN-FD if this
                # parameter was not specified.
                return 8

            # bus is not CAN
            return None

        val = com_param.value
        if not isinstance(val, str):
            return None

        m = re.search("TX_DL *= *([0-9]*)", val)
        if m:
            return int(m.group(1))

        # unexpected format of parameter value
        return 8

    def uses_can(self, protocol: Optional[Union[str, "Protocol"]] = None) -> bool:
        """
        Check if CAN ought to be used as the link layer protocol.
        """
        return self.get_can_receive_id(protocol=protocol) is not None

    def uses_can_fd(self, protocol: Optional[Union[str, "Protocol"]] = None) -> bool:
        """Check if CAN-FD ought to be used.

        If the ECU is not using CAN-FD for the specified protocol, `False`
        is returned.

        If this method returns `True`, `.uses_can() == True` is implied
        for the protocol.
        """

        if not self.uses_can(protocol):
            return False

        com_param = self.get_comparam("CP_CANFDTxMaxDataLength", protocol=protocol)
        if com_param is None:
            return False

        return "CANFD" in com_param.value

    def get_can_baudrate(self, protocol: Optional[Union[str, "Protocol"]] = None) -> Optional[int]:
        """Baudrate of the CAN bus which is used by the ECU [bits/s]

        If the ECU is not using CAN for the specified protocol, None
        is returned.

        """
        com_param = self.get_comparam("CP_Baudrate", protocol=protocol)
        if com_param is None:
            return None

        val = com_param.value
        if not isinstance(val, str):
            return None

        return int(val)

    def get_can_fd_baudrate(self,
                            protocol: Optional[Union[str, "Protocol"]] = None) -> Optional[int]:
        """Data baudrate of the CAN bus which is used by the ECU [bits/s]

        If the ECU is not using CAN-FD for the specified protocol,
        None is returned.
        """
        if not self.uses_can_fd(protocol=protocol):
            return None

        com_param = self.get_comparam("CP_CANFDBaudrate", protocol=protocol)
        if com_param is None:
            return None

        val = com_param.value
        if not isinstance(val, str):
            return None

        return int(val)

    def get_can_receive_id(self,
                           protocol: Optional[Union[str, "Protocol"]] = None) -> Optional[int]:
        """CAN ID to which the ECU listens for diagnostic messages"""
        com_param = self.get_comparam("CP_UniqueRespIdTable", protocol=protocol)
        if com_param is None:
            return None

        with warnings.catch_warnings():
            # depending on the protocol, we may get
            # "Communication parameter 'CP_UniqueRespIdTable' does not
            # specify 'CP_CanPhysReqId'" warning here. we don't want this
            # warning and simply return None...
            warnings.simplefilter("ignore", category=OdxWarning)
            result = com_param.get_subvalue("CP_CanPhysReqId")
        if result is None:
            return None
        odxassert(isinstance(result, str))

        return int(result)

    def get_can_send_id(self, protocol: Optional[Union[str, "Protocol"]] = None) -> Optional[int]:
        """CAN ID to which the ECU sends replies to diagnostic messages"""

        # this hopefully resolves to the 'CP_UniqueRespIdTable'
        # parameter from the ISO_15765_2 comparam subset. (There is a
        # parameter with the same name in the ISO_13400_2_DIS_2015
        # subset for DoIP. If the wrong one is retrieved, try
        # specifying the protocol.)
        com_param = self.get_comparam("CP_UniqueRespIdTable", protocol=protocol)
        if com_param is None:
            return None

        with warnings.catch_warnings():
            # depending on the protocol, we may get
            # "Communication parameter 'CP_UniqueRespIdTable' does not
            # specify 'CP_CanRespUSDTId'" warning here. we don't want this
            # warning and simply return None...
            warnings.simplefilter("ignore", category=OdxWarning)
            result = com_param.get_subvalue("CP_CanRespUSDTId")
        if result is None:
            return None
        odxassert(isinstance(result, str))

        return int(result)

    def get_can_func_req_id(self,
                            protocol: Optional[Union[str, "Protocol"]] = None) -> Optional[int]:
        """CAN Functional Request Id."""
        com_param = self.get_comparam("CP_CanFuncReqId", protocol=protocol)
        if com_param is None:
            return None

        result = com_param.get_value()
        if result is None:
            return None
        odxassert(isinstance(result, str))

        return int(result)

    def get_doip_logical_ecu_address(self,
                                     protocol: Optional[Union[str,
                                                              "Protocol"]] = None) -> Optional[int]:
        """Return the address of the ECU when using functional addressing.

        The parameter protocol is used to distinguish between
        different interfaces, e.g., offboard and onboard DoIP
        Ethernet.
        """

        # this hopefully resolves to the 'CP_UniqueRespIdTable'
        # parameter from the ISO_13400_2_DIS_2015 comparam
        # subset. (There is a parameter with the same name in the
        # ISO_15765_2 subset for CAN. If the wrong one is retrieved,
        # try specifying the protocol.)
        com_param = self.get_comparam("CP_UniqueRespIdTable", protocol=protocol)

        if com_param is None:
            return None

        # The CP_DoIPLogicalEcuAddress is specified by the
        # "CP_DoIPLogicalEcuAddress" subvalue of the complex comparam
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
                                         protocol: Optional[Union[str, "Protocol"]] = None
                                        ) -> Optional[int]:
        """The logical gateway address for the diagnosis over IP transport protocol"""

        # retrieve CP_DoIPLogicalGatewayAddress from the
        # ISO_13400_2_DIS_2015 subset. hopefully.
        com_param = self.get_comparam("CP_DoIPLogicalGatewayAddress", protocol=protocol)
        if com_param is None:
            return None

        result = com_param.get_value()
        if result is None:
            return None
        odxassert(isinstance(result, str))

        return int(result)

    def get_doip_logical_tester_address(self,
                                        protocol: Optional[Union[str, "Protocol"]] = None
                                       ) -> Optional[int]:
        """DoIp logical gateway address"""

        # retrieve CP_DoIPLogicalTesterAddress from the
        # ISO_13400_2_DIS_2015 subset. hopefully.
        com_param = self.get_comparam("CP_DoIPLogicalTesterAddress", protocol=protocol)
        if com_param is None:
            return None

        result = com_param.get_value()
        if result is None:
            return None
        odxassert(isinstance(result, str))

        return int(result)

    def get_doip_logical_functional_address(self,
                                            protocol: Optional[Union[str, "Protocol"]] = None
                                           ) -> Optional[int]:
        """The logical functional DoIP address of the ECU."""

        # retrieve CP_DoIPLogicalFunctionalAddress from the
        # ISO_13400_2_DIS_2015 subset. hopefully.
        com_param = self.get_comparam(
            "CP_DoIPLogicalFunctionalAddress",
            protocol=protocol,
        )
        if com_param is None:
            return None

        result = com_param.get_value()
        if result is None:
            return None
        odxassert(isinstance(result, str))

        return int(result)

    def get_doip_routing_activation_timeout(self,
                                            protocol: Optional[Union[str, "Protocol"]] = None
                                           ) -> Optional[float]:
        """The timout for the DoIP routing activation request in seconds"""

        # retrieve CP_DoIPRoutingActivationTimeout from the
        # ISO_13400_2_DIS_2015 subset. hopefully.
        com_param = self.get_comparam("CP_DoIPRoutingActivationTimeout", protocol=protocol)
        if com_param is None:
            return None

        result = com_param.get_value()
        if result is None:
            return None
        odxassert(isinstance(result, str))

        return float(result) / 1e6

    def get_doip_routing_activation_type(self,
                                         protocol: Optional[Union[str, "Protocol"]] = None
                                        ) -> Optional[int]:
        """The DoIP routing activation type

        The number returned has the following meaning:

        0          Default
        1          WWH-OBD (worldwide harmonized onboard diagnostic).
        2-0xDF     reserved
        0xE0-0xFF  OEM-specific
        """

        # retrieve CP_DoIPRoutingActivationType from the
        # ISO_13400_2_DIS_2015 subset. hopefully.
        com_param = self.get_comparam("CP_DoIPRoutingActivationType", protocol=protocol)
        if com_param is None:
            return None

        result = com_param.get_value()
        if result is None:
            return None
        odxassert(isinstance(result, str))

        return int(result)

    def get_tester_present_time(self,
                                protocol: Optional[Union[str,
                                                         "Protocol"]] = None) -> Optional[float]:
        """Timeout on inactivity in seconds.

        This is defined by the communication parameter "CP_TesterPresentTime".

        Description of the comparam: "Time between a response and the
        next subsequent tester present message (if no other request is
        sent to this ECU) in case of physically addressed requests."
        """

        # retrieve CP_TesterPresentTime from either the
        # ISO_13400_2_DIS_2015 or the ISO_15765_2 subset.
        com_param = self.get_comparam("CP_TesterPresentTime", protocol=protocol)
        if com_param is None:
            return None

        result = com_param.get_value()
        if result is None:
            return None
        odxassert(isinstance(result, str))

        # the comparam specifies microseconds. convert this to seconds
        return float(result) / 1e6

    #####
    # </communication parameter handling>
    #####
