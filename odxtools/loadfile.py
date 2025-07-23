# SPDX-License-Identifier: MIT
import os
from pathlib import Path

from .database import Database


def load_pdx_file(pdx_file: str | Path) -> Database:
    db = Database()
    db.add_pdx_file(str(pdx_file))
    db.refresh()
    return db


def load_odx_d_file(odx_d_file_name: str | Path) -> Database:
    db = Database()
    db.add_odx_file(str(odx_d_file_name))
    db.refresh()

    return db


def load_file(file_name: str | Path) -> Database:
    if str(file_name).lower().endswith(".pdx"):
        return load_pdx_file(str(file_name))
    elif Path(file_name).suffix.lower().startswith(".odx"):
        return load_odx_d_file(str(file_name))
    else:
        raise RuntimeError(f"Could not guess the file format of file '{file_name}'!")


def load_files(*file_names: str | Path) -> Database:
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


def load_directory(dir_name: str | Path) -> Database:
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
