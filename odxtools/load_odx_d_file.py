# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from .database import Database
from .globals import logger

def load_odx_d_file(odx_d_file_name: str, enable_candela_workarounds: bool = True):
    container = Database(odx_d_file_name=odx_d_file_name,
                         enable_candela_workarounds=enable_candela_workarounds)
    logger.info(f"--- --- --- Done with parsing --- --- ---")
    return container
