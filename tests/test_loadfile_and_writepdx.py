# SPDX-License-Identifier: MIT
"""Tests for the loading helpers and the PDX writer."""

from __future__ import annotations

import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import odxtools
from odxtools.loadfile import load_directory, load_file, load_files, load_pdx_file
from odxtools.writepdxfile import make_bool_xml_attrib, make_xml_attrib, write_pdx_file

SOMERSAULT_PDX = Path("./examples/somersault.pdx")


class TestLoadFileHelpers(unittest.TestCase):

    def test_load_pdx_via_load_file(self) -> None:
        db = load_file(SOMERSAULT_PDX)
        self.assertIn("somersault_lazy", [ecu.short_name for ecu in db.ecu_variants])

    def test_load_file_rejects_unknown_extension(self) -> None:
        # load_file dispatches on the suffix, so anything it cannot recognize
        # must be refused rather than silently parsed as ODX.
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
                    suffix = Path(name).suffix.lower()
                    # The auxiliary files have to come along: the single-ECU
                    # jobs of the somersault database refer to jobs.py, and
                    # loading fails if the referenced files are absent.
                    if (name.lower().endswith("index.xml") or suffix.startswith(".odx") or
                            suffix in {".py", ".txt", ".bin"}):
                        zf.extract(name, tmp_path)

            db = load_directory(tmp_path)
            self.assertGreater(len(db.diag_layer_containers), 0)
            self.assertGreater(len(db.ecu_variants), 0)


class TestWritePdxHelpers(unittest.TestCase):

    def test_make_xml_attrib(self) -> None:
        # None means "attribute not present at all", and values have to be
        # escaped so that a quote cannot break out of the attribute.
        self.assertEqual(make_xml_attrib("FOO", None), "")
        self.assertEqual(make_xml_attrib("FOO", "bar"), ' FOO="bar"')
        self.assertEqual(make_xml_attrib("FOO", 'a"b'), ' FOO="a&quot;b"')

    def test_make_bool_xml_attrib(self) -> None:
        # False is still an explicit value and must be written out; only None
        # omits the attribute.
        self.assertEqual(make_bool_xml_attrib("FLAG", None), "")
        self.assertIn("FLAG", make_bool_xml_attrib("FLAG", True))
        self.assertIn("FLAG", make_bool_xml_attrib("FLAG", False))


class TestWritePdx(unittest.TestCase):

    def test_write_produces_a_well_formed_archive(self) -> None:
        original = load_pdx_file(SOMERSAULT_PDX)
        dlc_names = {dlc.short_name for dlc in original.diag_layer_containers}

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            out_path = os.path.join(tmp, "written.pdx")
            self.assertTrue(write_pdx_file(out_path, original))

            with zipfile.ZipFile(out_path, "r") as zf:
                names = set(zf.namelist())
                self.assertIn("index.xml", names)
                self.assertTrue(any(n.endswith(".odx-d") for n in names))

                # Every diagnostic layer container of the source database has
                # to be referenced from the index, otherwise the archive is
                # readable but incomplete.
                index_text = ElementTree.tostring(
                    ElementTree.fromstring(zf.read("index.xml")), encoding="unicode")
                for dlc_name in dlc_names:
                    self.assertIn(dlc_name, index_text)

    def test_write_then_reload_keeps_the_ecu_variants(self) -> None:
        original = load_pdx_file(SOMERSAULT_PDX)

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            out_path = os.path.join(tmp, "roundtrip.pdx")
            self.assertTrue(write_pdx_file(out_path, original))

            # Reload in strict mode: the written archive has to resolve all of
            # its references on its own, without falling back to lenient
            # parsing.
            reloaded = load_pdx_file(out_path)

        self.assertEqual(
            sorted(ecu.short_name for ecu in original.ecu_variants),
            sorted(ecu.short_name for ecu in reloaded.ecu_variants))

    def test_package_level_write_pdx_file(self) -> None:
        # odxtools.write_pdx_file is the documented entry point and is expected
        # to stay in sync with the implementation it re-exports.
        db = odxtools.load_pdx_file(SOMERSAULT_PDX)
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            out_path = os.path.join(tmp, "via_package.pdx")
            self.assertTrue(odxtools.write_pdx_file(out_path, db))
            with zipfile.ZipFile(out_path, "r") as zf:
                self.assertIn("index.xml", zf.namelist())


if __name__ == "__main__":
    unittest.main()
