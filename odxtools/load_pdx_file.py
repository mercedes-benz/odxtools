# SPDX-License-Identifier: MIT
from zipfile import ZipFile

from .database import Database


def load_pdx_file(pdx_file: str) -> Database:
    return Database(pdx_zip=ZipFile(pdx_file))
