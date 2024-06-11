# SPDX-License-Identifier: MIT
import os
from pathlib import Path
from typing import Union

from .database import Database


def load_pdx_file(pdx_file: Union[str, Path]) -> Database:
    db = Database()
    db.add_pdx_file(str(pdx_file))
    db.refresh()
    return db


def load_odx_d_file(odx_d_file_name: Union[str, Path]) -> Database:
    db = Database()
    db.add_odx_file(str(odx_d_file_name))
    db.refresh()

    return db


def load_file(file_name: Union[str, Path]) -> Database:
    if str(file_name).lower().endswith(".pdx"):
        return load_pdx_file(str(file_name))
    elif str(file_name).lower().endswith(".odx-d"):
        return load_odx_d_file(str(file_name))
    else:
        raise RuntimeError(f"Could not guess the file format of file '{file_name}'!")


def load_files(*file_names: Union[str, Path]) -> Database:
    db = Database()
    for file_name in file_names:
        p = Path(file_name)
        if p.suffix.lower() == ".pdx":
            db.add_pdx_file(str(file_name))
        elif p.suffix.lower().startswith(".odx"):
            db.add_odx_file(str(file_name))
        elif p.name.lower() != "index.xml":
            db.add_auxiliary_file(str(file_name))

    db.refresh()
    return db


def load_directory(dir_name: Union[str, Path]) -> Database:
    db = Database()
    for file_name in os.listdir(str(dir_name)):
        p = Path(dir_name) / file_name

        if not p.is_file():
            continue

        if p.suffix.lower() == ".pdx":
            db.add_pdx_file(str(p))
        elif p.suffix.lower().startswith(".odx"):
            db.add_odx_file(str(p))
        elif p.name.lower() != "index.xml":
            db.add_auxiliary_file(p.name, open(str(p), "rb"))

    db.refresh()
    return db
