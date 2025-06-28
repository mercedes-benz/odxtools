# SPDX-License-Identifier: MIT
from copy import copy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any
from xml.etree import ElementTree

from .additionalaudience import AdditionalAudience
from .diagdatadictionaryspec import DiagDataDictionarySpec
from .diaglayers.ecushareddata import EcuSharedData
from .functionalclass import FunctionalClass
from .multipleecujob import MultipleEcuJob
from .nameditemlist import NamedItemList
from .odxcategory import OdxCategory
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict

if TYPE_CHECKING:
    from .database import Database


@dataclass(kw_only=True)
class MultipleEcuJobSpec(OdxCategory):
    multiple_ecu_jobs: NamedItemList[MultipleEcuJob] = field(default_factory=NamedItemList)
    diag_data_dictionary_spec: DiagDataDictionarySpec | None = None
    functional_classes: NamedItemList[FunctionalClass] = field(default_factory=NamedItemList)
    additional_audiences: NamedItemList[AdditionalAudience] = field(default_factory=NamedItemList)
    import_refs: list[OdxLinkRef] = field(default_factory=list)

    @property
    def imported_layers(self) -> NamedItemList[EcuSharedData]:
        """The resolved IMPORT-REFs

        ODXLINK defined by ECU-SHARED-DATA layers referenced via
        IMPORT-REF ought to be treated as if they where defined
        locally.
        """
        return self._imported_layers

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "MultipleEcuJobSpec":

        base_obj = OdxCategory.from_et(et_element, context)
        kwargs = dataclass_fields_asdict(base_obj)

        multiple_ecu_jobs = NamedItemList([
            MultipleEcuJob.from_et(el, context)
            for el in et_element.iterfind("MULTIPLE-ECU-JOBS/MULTIPLE-ECU-JOB")
        ])
        diag_data_dictionary_spec = None
        if (ddds_elem := et_element.find("DIAG-DATA-DICTIONARY-SPEC")) is not None:
            diag_data_dictionary_spec = DiagDataDictionarySpec.from_et(ddds_elem, context)
        functional_classes = NamedItemList([
            FunctionalClass.from_et(el, context)
            for el in et_element.iterfind("FUNCT-CLASSS/FUNCT-CLASS")
        ])
        additional_audiences = NamedItemList([
            AdditionalAudience.from_et(el, context)
            for el in et_element.iterfind("ADDITIONAL-AUDIENCES/ADDITIONAL-AUDIENCE")
        ])
        import_refs = [
            OdxLinkRef.from_et(el, context) for el in et_element.iterfind("IMPORT-REFS/IMPORT-REF")
        ]

        return MultipleEcuJobSpec(
            multiple_ecu_jobs=multiple_ecu_jobs,
            diag_data_dictionary_spec=diag_data_dictionary_spec,
            functional_classes=functional_classes,
            additional_audiences=additional_audiences,
            import_refs=import_refs,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks = super()._build_odxlinks()

        for multiple_ecu_job in self.multiple_ecu_jobs:
            odxlinks.update(multiple_ecu_job._build_odxlinks())

        if self.diag_data_dictionary_spec is not None:
            odxlinks.update(self.diag_data_dictionary_spec._build_odxlinks())

        for functional_class in self.functional_classes:
            odxlinks.update(functional_class._build_odxlinks())

        for additional_audience in self.additional_audiences:
            odxlinks.update(additional_audience._build_odxlinks())

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        # deal with the import refs: IDs defined therein are to be
        # handled like they were local.
        self._imported_layers: NamedItemList[EcuSharedData] = NamedItemList()
        if self.import_refs:
            extended_odxlinks = copy(odxlinks)
            imported_links: dict[OdxLinkId, Any] = {}
            for import_ref in self.import_refs:
                imported_dl = odxlinks.resolve(import_ref, EcuSharedData)
                self._imported_layers.append(imported_dl)

                # replace the document fragments of the ODX id with
                # the those of the muliple-ecu-spec. (be aware that
                # the "original" locations are still available.)
                imported_dl_links = imported_dl._build_odxlinks()
                for link_id, obj in imported_dl_links.items():
                    link_id = OdxLinkId(link_id.local_id, self.odx_id.doc_fragments)
                    imported_links[link_id] = obj

                extended_odxlinks.update(imported_links, overwrite=False)
        else:
            extended_odxlinks = odxlinks

        for multiple_ecu_job in self.multiple_ecu_jobs:
            multiple_ecu_job._resolve_odxlinks(extended_odxlinks)

        if self.diag_data_dictionary_spec is not None:
            self.diag_data_dictionary_spec._resolve_odxlinks(extended_odxlinks)

        for functional_class in self.functional_classes:
            functional_class._resolve_odxlinks(extended_odxlinks)

        for additional_audiences in self.additional_audiences:
            additional_audiences._resolve_odxlinks(extended_odxlinks)

    def _finalize_init(self, database: "Database", odxlinks: OdxLinkDatabase) -> None:
        super()._finalize_init(database, odxlinks)

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        super()._resolve_snrefs(context)

        for multiple_ecu_job in self.multiple_ecu_jobs:
            multiple_ecu_job._resolve_snrefs(context)

        if self.diag_data_dictionary_spec is not None:
            self.diag_data_dictionary_spec._resolve_snrefs(context)

        for functional_class in self.functional_classes:
            functional_class._resolve_snrefs(context)

        for additional_audiences in self.additional_audiences:
            additional_audiences._resolve_snrefs(context)
