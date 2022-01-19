# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from zipfile import ZipFile

from .database import Database
from .globals import logger

def load_pdx_file(pdx_file: str, enable_candela_workarounds: bool = True):
    u = ZipFile(pdx_file)
    container = Database(pdx_zip=u, enable_candela_workarounds=enable_candela_workarounds)
    logger.info(f"--- --- --- Done with parsing --- --- ---")
    return container
