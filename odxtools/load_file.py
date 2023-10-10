# SPDX-License-Identifier: MIT
from .database import Database
from .load_odx_d_file import load_odx_d_file
from .load_pdx_file import load_pdx_file


def load_file(file_name: str) -> Database:
    if file_name.lower().endswith(".pdx"):
        return load_pdx_file(file_name)
    elif file_name.lower().endswith(".odx-d"):
        return load_odx_d_file(file_name)
    else:
        raise RuntimeError(f"Could not guess the file format of file '{file_name}'!")
