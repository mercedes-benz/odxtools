# SPDX-License-Identifier: MIT
from .database import Database


def load_odx_d_file(odx_d_file_name: str) -> Database:
    return Database(odx_d_file_name=odx_d_file_name)
