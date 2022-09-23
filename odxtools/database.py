# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Union
from xml.etree import ElementTree
from itertools import chain
from zipfile import ZipFile

from .diaglayer import DiagLayer, DiagLayerContainer, read_diag_layer_container_from_odx
from .globals import logger
from .nameditemlist import NamedItemList

class Database:
    """This class internalizes the diagnostic database for various ECUs
    described by a collection of ODX files which are usually collated
    into a single PDX file.
    """

    def __init__(self,
                 pdx_zip: ZipFile = None,
                 odx_d_file_name: str = None,
                 enable_candela_workarounds: bool = True):

        self._id_lookup: Dict[str, Any] = {}
        dlc_elements = []

        if pdx_zip is None and odx_d_file_name is None:
            # create an empty database object
            return

        if pdx_zip is not None and odx_d_file_name is not None:
            raise TypeError("The 'pdx_zip' and 'odx_d_file_name' parameters are mutually exclusive")

        if pdx_zip is not None:
            names = list(pdx_zip.namelist())
            names.sort()
            for zip_member in names:
                # file name can end with .odx, .odx-d, .odx-c, .odx-cs, .odx-e, .odx-f, .odx-fd, .odx-m, .odx-v
                # We could test for all that, or just make sure suffix starts with .odx
                if Path(zip_member).suffix.startswith(".odx"):
                    logger.info(f"Processing the file {zip_member}")
                    d = pdx_zip.read(zip_member)
                    root = ElementTree.fromstring(d)
                    dlc = root.find("DIAG-LAYER-CONTAINER")
                    if dlc is not None:
                        dlc_elements.append(dlc)

            tmp = [
                read_diag_layer_container_from_odx(dlc_el, enable_candela_workarounds=enable_candela_workarounds) \
                  for dlc_el in dlc_elements
            ]
            self._diag_layer_containers = NamedItemList(lambda x: x.short_name, tmp)
            self._diag_layer_containers.sort(key=lambda x: x.short_name)
            self.finalize_init()

        elif odx_d_file_name is not None:
            dlc_element = ElementTree.parse(odx_d_file_name).find("DIAG-LAYER-CONTAINER")

            self._diag_layer_containers = \
                NamedItemList(lambda x: x.short_name,
                              [read_diag_layer_container_from_odx(dlc_element)])
            self.finalize_init()

    def finalize_init(self):
        # Create wrapper objects
        self._diag_layers = NamedItemList(
            lambda dl: dl.short_name,
            chain(*(dlc.diag_layers for dlc in self.diag_layer_containers)))
        self._ecus = NamedItemList(
            lambda ecu: ecu.short_name,
            chain(*(dlc.ecu_variants for dlc in self.diag_layer_containers)))

        # Build id_lookup
        self._id_lookup = {}

        @lru_cache(maxsize=None)
        def get_lookups(layer: Union[DiagLayerContainer, DiagLayer], docnames = None) -> dict:
            lookup = layer._build_id_lookup()
            docnames = set(docnames or [])
            docnames.add(layer.short_name)
            result = dict(lookup)
            for key, value in dict(lookup).items():
                # In case an ID-REF uses a DOCREF
                for docname in docnames:
                    result[f"{key}_from_{docname}"] = value
            return result

        for dlc in self.diag_layer_containers:
            self.id_lookup.update(get_lookups(dlc))

            for dl in dlc.diag_layers:
                self.id_lookup.update(get_lookups(dl, tuple([dlc.short_name])))
        
        # Resolve references
        for dlc in self.diag_layer_containers:
            dlc._resolve_references(self.id_lookup)

        docref_lookup = {k: v for k, v in self.id_lookup.items() if '_from_' in k}

        for dl_type_name in ["ECU-SHARED-DATA", "PROTOCOL", "FUNCTIONAL-GROUP", "BASE-VARIANT", "ECU-VARIANT"]:
            dl: DiagLayer
            for dl in self.diag_layers:
                if dl.variant_type == dl_type_name:
                    dl_lookup = dict(docref_lookup)
                    for parent_ref in dl.parent_refs:
                        parent_ref._resolve_references(self.id_lookup)
                        dl_lookup.update(get_lookups(parent_ref.referenced_diag_layer))
                    for import_ref in dl.import_refs:
                        ecu_shared_data: DiagLayer = self.id_lookup.get(import_ref)
                        dl_lookup.update(get_lookups(ecu_shared_data))
                    # Locally defined takes precedence
                    dl_lookup.update(get_lookups(dl))
                    
                    dl._resolve_references(dl_lookup)

        get_lookups.cache_clear()

    @property
    def id_lookup(self) -> dict:
        """A map from id to object"""
        return self._id_lookup

    @property
    def ecus(self) -> NamedItemList[DiagLayer]:
        """ECU-variants defined in the data base"""
        return self._ecus

    @property
    def diag_layers(self) -> NamedItemList[DiagLayer]:
        """all diagnostic layers defined in the data base"""
        return self._diag_layers

    @property
    def diag_layer_containers(self):
        return self._diag_layer_containers

    @diag_layer_containers.setter
    def diag_layer_containers(self, value):
        self._diag_layer_containers = value
