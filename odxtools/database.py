# SPDX-License-Identifier: MIT
from itertools import chain
from pathlib import Path
from typing import List, Optional
from xml.etree import ElementTree
from zipfile import ZipFile

from packaging.version import Version

from .comparamspec import ComparamSpec
from .comparamsubset import ComparamSubset
from .diaglayer import DiagLayer
from .diaglayercontainer import DiagLayerContainer
from .exceptions import odxraise
from .nameditemlist import NamedItemList
from .odxlink import OdxLinkDatabase


class Database:
    """This class internalizes the diagnostic database for various ECUs
    described by a collection of ODX files which are usually collated
    into a single PDX file.
    """

    def __init__(self,
                 *,
                 pdx_zip: Optional[ZipFile] = None,
                 odx_d_file_name: Optional[str] = None) -> None:
        self.model_version = None

        if pdx_zip is None and odx_d_file_name is None:
            # create an empty database object
            self._diag_layer_containers = NamedItemList[DiagLayerContainer]()
            self._comparam_subsets = NamedItemList[ComparamSubset]()
            self._comparam_specs = NamedItemList[ComparamSpec]()
            return

        if pdx_zip is not None and odx_d_file_name is not None:
            raise TypeError("The 'pdx_zip' and 'odx_d_file_name' parameters are mutually exclusive")

        documents: List[ElementTree.Element] = []
        if pdx_zip is not None:
            names = list(pdx_zip.namelist())
            names.sort()
            for zip_member in names:
                # The name of ODX files can end with .odx, .odx-d,
                # .odx-c, .odx-cs, .odx-e, .odx-f, .odx-fd, .odx-m,
                # .odx-v .  We could test for all that, or just make
                # sure that the file's suffix starts with .odx
                if Path(zip_member).suffix.startswith(".odx"):
                    d = pdx_zip.read(zip_member)
                    root = ElementTree.fromstring(d)
                    documents.append(root)

        elif odx_d_file_name is not None:
            documents.append(ElementTree.parse(odx_d_file_name).getroot())

        dlcs: List[DiagLayerContainer] = []
        comparam_subsets: List[ComparamSubset] = []
        comparam_specs: List[ComparamSpec] = []
        for root in documents:
            # ODX spec version
            model_version = Version(root.attrib.get("MODEL-VERSION", "2.0"))
            if self.model_version is not None and self.model_version != model_version:
                odxraise(f"Different ODX versions used in the same file (ODX {model_version} "
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

        self._diag_layer_containers = NamedItemList(dlcs)
        self._comparam_subsets = NamedItemList(comparam_subsets)
        self._comparam_specs = NamedItemList(comparam_specs)

        self.refresh()

    def refresh(self) -> None:
        # Create wrapper objects
        self._diag_layers = NamedItemList(
            chain(*[dlc.diag_layers for dlc in self.diag_layer_containers]))

        self._protocols = NamedItemList(
            chain(*[dlc.protocols for dlc in self.diag_layer_containers]))

        self._ecus = NamedItemList(chain(*[dlc.ecu_variants for dlc in self.diag_layer_containers]))

        # Build odxlinks
        self._odxlinks = OdxLinkDatabase()

        for subset in self.comparam_subsets:
            self._odxlinks.update(subset._build_odxlinks())

        for spec in self.comparam_specs:
            self._odxlinks.update(spec._build_odxlinks())

        for dlc in self.diag_layer_containers:
            self._odxlinks.update(dlc._build_odxlinks())

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
            dlc._finalize_init(self._odxlinks)

    @property
    def odxlinks(self) -> OdxLinkDatabase:
        """A map from odx_id to object"""
        return self._odxlinks

    @property
    def protocols(self) -> NamedItemList[DiagLayer]:
        """
        All protocols defined by this database
        """
        return self._protocols

    @property
    def ecus(self) -> NamedItemList[DiagLayer]:
        """ECU-variants defined in the database"""
        return self._ecus

    @property
    def diag_layers(self) -> NamedItemList[DiagLayer]:
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
