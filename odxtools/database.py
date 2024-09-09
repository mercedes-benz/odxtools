# SPDX-License-Identifier: MIT
from itertools import chain
from os import PathLike
from pathlib import Path
from typing import IO, Any, Dict, List, Optional, OrderedDict, Union
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
from .exceptions import odxraise, odxrequire
from .nameditemlist import NamedItemList
from .odxlink import OdxLinkDatabase, OdxLinkId


class Database:
    """This class internalizes the diagnostic database for various ECUs
    described by a collection of ODX files which are usually collated
    into a single PDX file.
    """

    def __init__(self) -> None:
        self.model_version: Optional[Version] = None
        self.auxiliary_files: OrderedDict[str, IO[bytes]] = OrderedDict()

        # create an empty database object
        self._diag_layer_containers = NamedItemList[DiagLayerContainer]()
        self._comparam_subsets = NamedItemList[ComparamSubset]()
        self._comparam_specs = NamedItemList[ComparamSpec]()
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
                self._process_xml_tree(root)
            elif p.name.lower() == "index.xml":
                root = ElementTree.parse(pdx_zip.open(zip_member)).getroot()
                db_short_name = odxrequire(root.findtext("SHORT-NAME"))
                self.short_name = db_short_name
            else:
                self.add_auxiliary_file(zip_member, pdx_zip.open(zip_member))

    def add_odx_file(self, odx_file_name: Union[str, "PathLike[Any]"]) -> None:
        self._process_xml_tree(ElementTree.parse(odx_file_name).getroot())

    def add_auxiliary_file(self,
                           aux_file_name: Union[str, "PathLike[Any]"],
                           aux_file_obj: Optional[IO[bytes]] = None) -> None:
        if aux_file_obj is None:
            aux_file_obj = open(aux_file_name, "rb")

        self.auxiliary_files[str(aux_file_name)] = aux_file_obj

    def _process_xml_tree(self, root: ElementTree.Element) -> None:
        dlcs: List[DiagLayerContainer] = []
        comparam_subsets: List[ComparamSubset] = []
        comparam_specs: List[ComparamSpec] = []

        # ODX spec version
        model_version = Version(root.attrib.get("MODEL-VERSION", "2.0"))
        if self.model_version is not None and self.model_version != model_version:
            odxraise(f"Different ODX versions used for the same database (ODX {model_version} "
                     f"and ODX {self.model_version}")

        self.model_version = model_version

        dlc = root.find("DIAG-LAYER-CONTAINER")
        if dlc is not None:
            dlcs.append(DiagLayerContainer.from_et(dlc, []))

        # In ODX 2.0 there was only COMPARAM-SPEC. In ODX 2.2 the
        # content of COMPARAM-SPEC was moved to COMPARAM-SUBSET
        # and COMPARAM-SPEC became a container for PROT-STACKS and
        # a PROT-STACK references a list of COMPARAM-SUBSET
        cp_subset = root.find("COMPARAM-SUBSET")
        if cp_subset is not None:
            comparam_subsets.append(ComparamSubset.from_et(cp_subset, []))

        cp_spec = root.find("COMPARAM-SPEC")
        if cp_spec is not None:
            if model_version < Version("2.2"):
                comparam_subsets.append(ComparamSubset.from_et(cp_spec, []))
            else:  # odx >= 2.2
                comparam_specs.append(ComparamSpec.from_et(cp_spec, []))

        self._diag_layer_containers.extend(dlcs)
        self._comparam_subsets.extend(comparam_subsets)
        self._comparam_specs.extend(comparam_specs)

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

        # let the diaglayers sort out the inherited objects and the
        # short name references
        for dlc in self.diag_layer_containers:
            dlc._finalize_init(self, self._odxlinks)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        result: Dict[OdxLinkId, Any] = {}

        for subset in self.comparam_subsets:
            result.update(subset._build_odxlinks())

        for spec in self.comparam_specs:
            result.update(spec._build_odxlinks())

        for dlc in self.diag_layer_containers:
            result.update(dlc._build_odxlinks())

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

    def __repr__(self) -> str:
        return f"Database(model_version={self.model_version}, " \
            f"protocols={[x.short_name for x in self.protocols]}, " \
            f"ecus={[x.short_name for x in self.ecus]}, " \
            f"diag_layer_containers={repr(self.diag_layer_containers)}, " \
            f"comparam_subsets={repr(self.comparam_subsets)}, " \
            f"comparam_specs={repr(self.comparam_specs)})"
