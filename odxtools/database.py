# SPDX-License-Identifier: MIT
from collections import OrderedDict
from itertools import chain
from os import PathLike
from pathlib import Path
from typing import IO, Any, Union
from xml.etree import ElementTree
from zipfile import ZipFile

from packaging.version import Version

from .comparamspec import ComparamSpec
from .comparamsubset import ComparamSubset
from .diaglayercontainer import DiagLayerContainer
from .diaglayers.basevariant import BaseVariant
from .diaglayers.diaglayer import DiagLayer
from .diaglayers.ecushareddata import EcuSharedData
from .diaglayers.ecuvariant import EcuVariant
from .diaglayers.functionalgroup import FunctionalGroup
from .diaglayers.protocol import Protocol
from .ecuconfig import EcuConfig
from .exceptions import odxraise, odxrequire
from .flash import Flash
from .functiondictionary import FunctionDictionary
from .multipleecujobspec import MultipleEcuJobSpec
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import DocType, OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .vehicleinfospec import VehicleInfoSpec


class Database:
    """This class internalizes the diagnostic database for various ECUs
    described by a collection of ODX files which are usually collated
    into a single PDX file.
    """

    def __init__(self) -> None:
        self.model_version: Version | None = None
        self.auxiliary_files: OrderedDict[str, IO[bytes]] = OrderedDict()

        # create an empty database object
        self._diag_layer_containers = NamedItemList[DiagLayerContainer]()
        self._comparam_subsets = NamedItemList[ComparamSubset]()
        self._comparam_specs = NamedItemList[ComparamSpec]()
        self._ecu_configs = NamedItemList[EcuConfig]()
        self._vehicle_info_specs = NamedItemList[VehicleInfoSpec]()
        self._flashs = NamedItemList[Flash]()
        self._multiple_ecu_job_specs = NamedItemList[MultipleEcuJobSpec]()
        self._function_dictionaries = NamedItemList[FunctionDictionary]()
        self._short_name = "odx_database"

    def add_pdx_file(self, pdx_file: Union[str, "PathLike[Any]", IO[bytes], ZipFile]) -> None:
        """Add PDX file to database.
        Either pass the path to the file, an IO with the file content or a ZipFile object.
        """
        if isinstance(pdx_file, ZipFile):
            pdx_zip = pdx_file
        else:
            pdx_zip = ZipFile(pdx_file)
        for zip_member in pdx_zip.namelist():
            # The name of ODX files can end with .odx, .odx-d,
            # .odx-c, .odx-cs, .odx-e, .odx-f, .odx-fd, .odx-m,
            # .odx-v .  We could test for all that, or just make
            # sure that the file's suffix starts with .odx
            p = Path(zip_member)
            if p.suffix.lower().startswith(".odx"):
                root = ElementTree.parse(pdx_zip.open(zip_member)).getroot()
                self.add_xml_tree(root)
            elif p.name.lower() == "index.xml":
                root = ElementTree.parse(pdx_zip.open(zip_member)).getroot()
                db_short_name = odxrequire(root.findtext("SHORT-NAME"))
                self.short_name = db_short_name
            else:
                self.add_auxiliary_file(zip_member, pdx_zip.open(zip_member))

    def add_odx_file(self, odx_file_name: Union[str, "PathLike[Any]"]) -> None:
        self.add_xml_tree(ElementTree.parse(odx_file_name).getroot())

    def add_auxiliary_file(self,
                           aux_file_name: Union[str, "PathLike[Any]"],
                           aux_file_obj: IO[bytes] | None = None) -> None:
        if aux_file_obj is None:
            aux_file_obj = open(aux_file_name, "rb")

        self.auxiliary_files[str(aux_file_name)] = aux_file_obj

    def add_xml_tree(self, root: ElementTree.Element) -> None:
        # ODX spec version
        model_version = Version(root.attrib.get("MODEL-VERSION", "2.0"))
        if self.model_version is not None and self.model_version != model_version:
            odxraise(f"Different ODX versions used for the same database (ODX {model_version} "
                     f"and ODX {self.model_version}")

        self.model_version = model_version

        child_elements = list(root)
        if len(child_elements) != 1:
            odxraise("Each ODX document must contain exactly one category.")

        category_et = child_elements[0]
        category_sn = odxrequire(category_et.findtext("SHORT-NAME"))
        category_tag = category_et.tag

        if category_tag == "DIAG-LAYER-CONTAINER":
            context = OdxDocContext(model_version,
                                    (OdxDocFragment(category_sn, DocType.CONTAINER),))
            self._diag_layer_containers.append(DiagLayerContainer.from_et(category_et, context))
        elif category_tag == "COMPARAM-SUBSET":
            context = OdxDocContext(model_version,
                                    (OdxDocFragment(category_sn, DocType.COMPARAM_SUBSET),))
            self._comparam_subsets.append(ComparamSubset.from_et(category_et, context))
        elif category_tag == "COMPARAM-SPEC":
            # In ODX 2.0 there was only COMPARAM-SPEC. In ODX 2.2 the
            # content of COMPARAM-SPEC was moved to COMPARAM-SUBSET
            # and COMPARAM-SPEC became a container for PROT-STACKS and
            # a PROT-STACK references a list of COMPARAM-SUBSET
            context = OdxDocContext(model_version,
                                    (OdxDocFragment(category_sn, DocType.COMPARAM_SPEC),))
            if model_version < Version("2.2"):
                self._comparam_subsets.append(ComparamSubset.from_et(category_et, context))
            else:
                self._comparam_specs.append(ComparamSpec.from_et(category_et, context))
        elif category_tag == "ECU-CONFIG":
            context = OdxDocContext(model_version,
                                    (OdxDocFragment(category_sn, DocType.ECU_CONFIG),))
            self._ecu_configs.append(EcuConfig.from_et(category_et, context))
        elif category_tag == "VEHICLE-INFO-SPEC":
            context = OdxDocContext(model_version,
                                    (OdxDocFragment(category_sn, DocType.VEHICLE_INFO_SPEC),))
            self._vehicle_info_specs.append(VehicleInfoSpec.from_et(category_et, context))
        elif category_tag == "FLASH":
            context = OdxDocContext(model_version, (OdxDocFragment(category_sn, DocType.FLASH),))
            self._flashs.append(Flash.from_et(category_et, context))
        elif category_tag == "MULTIPLE-ECU-JOB-SPEC":
            context = OdxDocContext(model_version,
                                    (OdxDocFragment(category_sn, DocType.MULTIPLE_ECU_JOB_SPEC),))
            self._multiple_ecu_job_specs.append(MultipleEcuJobSpec.from_et(category_et, context))
        elif category_tag == "FUNCTION-DICTIONARY":
            context = OdxDocContext(model_version, (OdxDocFragment(
                category_sn, DocType.FUNCTION_DICTIONARY_SPEC),))
            self._function_dictionaries.append(FunctionDictionary.from_et(category_et, context))
        else:
            odxraise(f"Encountered unknown ODX category '{category_tag}' (non-conforming dataset?)")

    def refresh(self) -> None:
        # Create wrapper objects
        self._diag_layers = NamedItemList(
            chain(*[dlc.diag_layers for dlc in self.diag_layer_containers]))

        self._ecu_shared_datas = NamedItemList(
            chain(*[dlc.ecu_shared_datas for dlc in self.diag_layer_containers]))
        self._protocols = NamedItemList(
            chain(*[dlc.protocols for dlc in self.diag_layer_containers]))
        self._functional_groups = NamedItemList(
            chain(*[dlc.functional_groups for dlc in self.diag_layer_containers]))
        self._base_variants = NamedItemList(
            chain(*[dlc.base_variants for dlc in self.diag_layer_containers]))
        self._ecu_variants = NamedItemList(
            chain(*[dlc.ecu_variants for dlc in self.diag_layer_containers]))

        # Build odxlinks
        self._odxlinks = OdxLinkDatabase()
        self._odxlinks.update(self._build_odxlinks())

        # Resolve ODXLINK references
        for subset in self.comparam_subsets:
            subset._resolve_odxlinks(self._odxlinks)

        for spec in self.comparam_specs:
            spec._resolve_odxlinks(self._odxlinks)

        for dlc in self.diag_layer_containers:
            dlc._resolve_odxlinks(self._odxlinks)

        for ecu_config in self.ecu_configs:
            ecu_config._resolve_odxlinks(self._odxlinks)

        for vehicle_info_spec in self.vehicle_info_specs:
            vehicle_info_spec._resolve_odxlinks(self._odxlinks)

        for flash in self.flashs:
            flash._resolve_odxlinks(self._odxlinks)

        for multiple_ecu_job_spec in self.multiple_ecu_job_specs:
            multiple_ecu_job_spec._resolve_odxlinks(self._odxlinks)

        for function_dictionary in self.function_dictionaries:
            function_dictionary._resolve_odxlinks(self._odxlinks)

        # resolve short name references for containers which do not do
        # inheritance (we can call directly call _resolve_snrefs())
        context = SnRefContext()
        context.database = self

        # let the diaglayers sort out the inherited objects
        for subset in self.comparam_subsets:
            subset._finalize_init(self, self._odxlinks)
        for spec in self.comparam_specs:
            spec._finalize_init(self, self._odxlinks)
        for dlc in self.diag_layer_containers:
            dlc._finalize_init(self, self._odxlinks)
        for ecu_config in self.ecu_configs:
            ecu_config._finalize_init(self, self._odxlinks)
        for vehicle_info_spec in self.vehicle_info_specs:
            vehicle_info_spec._finalize_init(self, self._odxlinks)
        for flash in self.flashs:
            flash._finalize_init(self, self._odxlinks)
        for multiple_ecu_job_spec in self.multiple_ecu_job_specs:
            multiple_ecu_job_spec._finalize_init(self, self._odxlinks)
        for function_dictionary in self.function_dictionaries:
            function_dictionary._finalize_init(self, self._odxlinks)

        for subset in self.comparam_subsets:
            subset._resolve_snrefs(context)
        for spec in self.comparam_specs:
            spec._resolve_snrefs(context)
        for dlc in self.diag_layer_containers:
            dlc._resolve_snrefs(context)
        for ecu_config in self.ecu_configs:
            ecu_config._resolve_snrefs(context)
        for vehicle_info_spec in self.vehicle_info_specs:
            vehicle_info_spec._resolve_snrefs(context)
        for flash in self.flashs:
            flash._resolve_snrefs(context)
        for multiple_ecu_job_spec in self.multiple_ecu_job_specs:
            multiple_ecu_job_spec._resolve_snrefs(context)
        for function_dictionary in self.function_dictionaries:
            function_dictionary._resolve_snrefs(context)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        result: dict[OdxLinkId, Any] = {}

        for subset in self.comparam_subsets:
            result.update(subset._build_odxlinks())

        for spec in self.comparam_specs:
            result.update(spec._build_odxlinks())

        for dlc in self.diag_layer_containers:
            result.update(dlc._build_odxlinks())

        for ecu_config in self.ecu_configs:
            result.update(ecu_config._build_odxlinks())

        for vehicle_info_spec in self.vehicle_info_specs:
            result.update(vehicle_info_spec._build_odxlinks())

        for flash in self.flashs:
            result.update(flash._build_odxlinks())

        for multiple_ecu_job_spec in self.multiple_ecu_job_specs:
            result.update(multiple_ecu_job_spec._build_odxlinks())

        for function_dictionary in self.function_dictionaries:
            result.update(function_dictionary._build_odxlinks())

        return result

    @property
    def odxlinks(self) -> OdxLinkDatabase:
        """A map from odx_id to object"""
        return self._odxlinks

    @property
    def short_name(self) -> str:
        return self._short_name

    @short_name.setter
    def short_name(self, value: str) -> None:
        self._short_name = value

    @property
    def ecu_shared_datas(self) -> NamedItemList[EcuSharedData]:
        """All ECU shared data layers defined by this database

        ECU shared data layers act as a kind of shared library for
        data that is common to multiple otherwise unrelated ECUs.

        """
        return self._ecu_shared_datas

    @property
    def protocols(self) -> NamedItemList[Protocol]:
        """All protocol layers defined by this database"""
        return self._protocols

    @property
    def functional_groups(self) -> NamedItemList["FunctionalGroup"]:
        """Functional group layers defined in the database"""
        return self._functional_groups

    @property
    def base_variants(self) -> NamedItemList["BaseVariant"]:
        """Base variants defined in the database"""
        return self._base_variants

    @property
    def ecus(self) -> NamedItemList["EcuVariant"]:
        """ECU variants defined in the database

        This property is an alias for `.ecu_variants`"""
        return self._ecu_variants

    @property
    def ecu_variants(self) -> NamedItemList["EcuVariant"]:
        """ECU variants defined in the database"""
        return self._ecu_variants

    @property
    def diag_layers(self) -> NamedItemList["DiagLayer"]:
        """All diagnostic layers defined in the database"""
        return self._diag_layers

    @property
    def diag_layer_containers(self) -> NamedItemList[DiagLayerContainer]:
        return self._diag_layer_containers

    @diag_layer_containers.setter
    def diag_layer_containers(self, value: NamedItemList[DiagLayerContainer]) -> None:
        self._diag_layer_containers = value

    @property
    def comparam_subsets(self) -> NamedItemList[ComparamSubset]:
        return self._comparam_subsets

    @property
    def comparam_specs(self) -> NamedItemList[ComparamSpec]:
        return self._comparam_specs

    @property
    def ecu_configs(self) -> NamedItemList[EcuConfig]:
        return self._ecu_configs

    @property
    def vehicle_info_specs(self) -> NamedItemList[VehicleInfoSpec]:
        return self._vehicle_info_specs

    @property
    def flashs(self) -> NamedItemList[Flash]:
        return self._flashs

    @property
    def multiple_ecu_job_specs(self) -> NamedItemList[MultipleEcuJobSpec]:
        return self._multiple_ecu_job_specs

    @property
    def function_dictionaries(self) -> NamedItemList[FunctionDictionary]:
        return self._function_dictionaries

    def __repr__(self) -> str:
        return f"Database(model_version={self.model_version}, " \
            f"protocols={[x.short_name for x in self.protocols]}, " \
            f"ecus={[x.short_name for x in self.ecus]}, " \
            f"diag_layer_containers={repr(self.diag_layer_containers)}, " \
            f"comparam_subsets={repr(self.comparam_subsets)}, " \
            f"comparam_specs={repr(self.comparam_specs)}, " \
            f"ecu_configs={repr(self.ecu_configs)}, " \
            f"vehicle_info_specs={repr(self.vehicle_info_specs)}, " \
            f"multiple_ecu_job_specs={repr(self.multiple_ecu_job_specs)}, " \
            f"function_dictionaries={repr(self.function_dictionaries)}, " \
            f"flashs={repr(self.flashs)})"
