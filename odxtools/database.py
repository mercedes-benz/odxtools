# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from functools import lru_cache
from pathlib import Path
from typing import Any, Optional, Dict, Union
from xml.etree import ElementTree
from itertools import chain
from zipfile import ZipFile

from .utils import short_name_as_id
from .odxlink import OdxLinkDatabase
from .diaglayer import DiagLayer, DiagLayerContainer, read_diag_layer_container_from_odx
from .globals import logger
from .nameditemlist import NamedItemList

class Database:
    """This class internalizes the diagnostic database for various ECUs
    described by a collection of ODX files which are usually collated
    into a single PDX file.
    """

    def __init__(self,
                 pdx_zip: Optional[ZipFile] = None,
                 odx_d_file_name: Optional[str] = None,
                 enable_candela_workarounds: bool = True):

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
                read_diag_layer_container_from_odx(dlc_el,
                                                   enable_candela_workarounds=enable_candela_workarounds) \
                  for dlc_el in dlc_elements
            ]
            self._diag_layer_containers = NamedItemList(short_name_as_id, tmp)
            self._diag_layer_containers.sort(key=short_name_as_id)
            self.finalize_init()

        elif odx_d_file_name is not None:
            dlc_element = ElementTree.parse(odx_d_file_name).find("DIAG-LAYER-CONTAINER")

            self._diag_layer_containers = \
                NamedItemList(short_name_as_id,
                              [read_diag_layer_container_from_odx(dlc_element)])
            self.finalize_init()

    def finalize_init(self) -> None:
        # Create wrapper objects
        self._diag_layers = NamedItemList(
            short_name_as_id,
            chain(*[dlc.diag_layers for dlc in self.diag_layer_containers]))
        self._ecus = NamedItemList(
            short_name_as_id,
            chain(*[dlc.ecu_variants for dlc in self.diag_layer_containers]))

        # Build odxlinks
        self._odxlinks = OdxLinkDatabase()

        for dlc in self.diag_layer_containers:
            self.odxlinks.update(dlc._build_odxlinks())

        for dl in self.diag_layers:
            self.odxlinks.update(dl._build_odxlinks())

        # Resolve references
        for dlc in self.diag_layer_containers:
            dlc._resolve_references(self.odxlinks)

        for dl_type_name in ["ECU-SHARED-DATA", "PROTOCOL", "FUNCTIONAL-GROUP", "BASE-VARIANT", "ECU-VARIANT"]:
            for dl in self.diag_layers:
                if dl.variant_type == dl_type_name:
                    dl._resolve_references(self.odxlinks)

    @property
    def odxlinks(self) -> OdxLinkDatabase:
        """A map from odx_id to object"""
        return self._odxlinks

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
