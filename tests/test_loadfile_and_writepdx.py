# SPDX-License-Identifier: MIT
"""Tests for load helpers and PDX writing.

These exercise low-coverage modules (`loadfile`, `writepdxfile`) that are
central to everyday odxtools usage.
"""

from __future__ import annotations

import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import odxtools
import odxtools.exceptions
from odxtools.loadfile import load_directory, load_file, load_files, load_pdx_file
from odxtools.writepdxfile import (
    make_bool_xml_attrib,
    make_xml_attrib,
    write_pdx_file,
)

SOMERSAULT_PDX = Path("./examples/somersault.pdx")


class TestLoadFileHelpers(unittest.TestCase):
    def test_load_pdx_via_load_file(self) -> None:
        db = load_file(SOMERSAULT_PDX)
        self.assertGreater(len(db.ecu_variants), 0)
        self.assertIn("somersault_lazy", [ecu.short_name for ecu in db.ecu_variants])

    def test_load_file_rejects_unknown_extension(self) -> None:
        with self.assertRaises(RuntimeError):
            load_file("not_a_database.txt")

    def test_load_files_single_pdx(self) -> None:
        db = load_files(SOMERSAULT_PDX)
        self.assertEqual(db.ecu_variants.somersault_lazy.short_name, "somersault_lazy")

    def test_load_directory_with_extracted_odx(self) -> None:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            tmp_path = Path(tmp)
            with zipfile.ZipFile(SOMERSAULT_PDX, "r") as zf:
                for name in zf.namelist():
                    lower = name.lower()
                    suffix = Path(name).suffix.lower()
                    # Include ODX categories, index, and referenced auxiliaries
                    # (e.g. jobs.py used by single-ECU jobs).
                    if (
                        lower.endswith("index.xml")
                        or suffix.startswith(".odx")
                        or suffix in {".py", ".txt", ".bin"}
                    ):
                        zf.extract(name, tmp_path)

            db = load_directory(tmp_path)
            self.assertGreater(len(db.diag_layer_containers), 0)
            self.assertGreater(len(db.ecu_variants), 0)


class TestWritePdxHelpers(unittest.TestCase):
    def test_make_xml_attrib(self) -> None:
        self.assertEqual(make_xml_attrib("FOO", None), "")
        self.assertEqual(make_xml_attrib("FOO", "bar"), ' FOO="bar"')
        self.assertEqual(make_xml_attrib("FOO", 'a"b'), ' FOO="a&quot;b"')

    def test_make_bool_xml_attrib(self) -> None:
        self.assertEqual(make_bool_xml_attrib("FLAG", None), "")
        self.assertIn("FLAG", make_bool_xml_attrib("FLAG", True))
        self.assertIn("FLAG", make_bool_xml_attrib("FLAG", False))


class TestWritePdx(unittest.TestCase):
    def test_write_somersault_produces_valid_pdx_archive(self) -> None:
        original = load_pdx_file(SOMERSAULT_PDX)
        dlc_names = {dlc.short_name for dlc in original.diag_layer_containers}

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            out_path = os.path.join(tmp, "written.pdx")
            self.assertTrue(write_pdx_file(out_path, original))
            self.assertTrue(os.path.isfile(out_path))

            with zipfile.ZipFile(out_path, "r") as zf:
                names = set(zf.namelist())
                self.assertIn("index.xml", names)
                self.assertTrue(any(n.endswith(".odx-d") for n in names))

                index_root = ElementTree.fromstring(zf.read("index.xml"))
                index_text = ElementTree.tostring(index_root, encoding="unicode")
                for dlc_name in dlc_names:
                    self.assertIn(dlc_name, index_text)

            # Reload in non-strict mode: write_pdx currently omits some
            # externally-referenced COMPARAM subsets present in the sample PDX.
            previous = odxtools.exceptions.strict_mode
            odxtools.exceptions.strict_mode = False
            try:
                reloaded = load_pdx_file(out_path)
            finally:
                odxtools.exceptions.strict_mode = previous

            self.assertEqual(
                sorted(ecu.short_name for ecu in original.ecu_variants),
                sorted(ecu.short_name for ecu in reloaded.ecu_variants),
            )

    def test_package_level_write_pdx_file(self) -> None:
        db = odxtools.load_pdx_file(SOMERSAULT_PDX)
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            out_path = os.path.join(tmp, "via_package.pdx")
            self.assertTrue(odxtools.write_pdx_file(out_path, db))

            with zipfile.ZipFile(out_path, "r") as zf:
                self.assertIn("index.xml", zf.namelist())


if __name__ == "__main__":
    unittest.main()
