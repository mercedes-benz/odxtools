# SPDX-License-Identifier: MIT
import datetime
import html
import inspect
import mimetypes
import os
import time
import zipfile
from typing import Any

import jinja2

import odxtools

from .database import Database
from .odxlink import DocType, OdxDocFragment, OdxLinkRef
from .odxtypes import bool_to_odxstr


def jinja2_odxraise_helper(msg: str) -> None:
    raise Exception(msg)


def make_xml_attrib(attrib_name: str, attrib_val: Any | None) -> str:
    if attrib_val is None:
        return ""

    return f' {attrib_name}="{html.escape(attrib_val)}"'


def make_bool_xml_attrib(attrib_name: str, attrib_val: bool | None) -> str:
    if attrib_val is None:
        return ""

    return make_xml_attrib(attrib_name, bool_to_odxstr(attrib_val))


def set_category_docfrag(jinja_vars: dict[str, Any], category_short_name: str,
                         category_type: str) -> str:
    jinja_vars["cur_docfrags"] = [OdxDocFragment(category_short_name, DocType(category_type))]

    return ""


def set_layer_docfrag(jinja_vars: dict[str, Any], layer_short_name: str | None) -> str:
    cur_docfrags = jinja_vars["cur_docfrags"]

    if layer_short_name is None:
        cur_docfrags = cur_docfrags[:1]
        return ""

    if len(cur_docfrags) == 1:
        cur_docfrags.append(OdxDocFragment(layer_short_name, DocType.LAYER))
    else:
        cur_docfrags[1] = OdxDocFragment(layer_short_name, DocType.LAYER)

    return ""


def make_ref_attribs(jinja_vars: dict[str, Any], ref: OdxLinkRef) -> str:
    cur_docfrags = jinja_vars["cur_docfrags"]

    for ref_frag in ref.ref_docs:
        if ref_frag in cur_docfrags:
            return f"ID-REF=\"{ref.ref_id}\""

    docfrag = ref.ref_docs[-1]
    return f"ID-REF=\"{ref.ref_id}\" DOCREF=\"{docfrag.doc_name}\" DOCTYPE=\"{docfrag.doc_type.value}\""


__module_filename = inspect.getsourcefile(odxtools)
assert isinstance(__module_filename, str)
__templates_dir = os.path.sep.join([os.path.dirname(__module_filename), "templates"])


def write_pdx_file(
    output_file_name: str,
    database: Database,
    templates_dir: str = __templates_dir,
) -> bool:
    """
    Write an internalized database to a PDX file.
    """
    file_index = []
    with zipfile.ZipFile(output_file_name, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:

        # write all files in the templates directory
        for root, _, files in os.walk(templates_dir):
            for template_file_name in files:
                # we are not interested in the autosave garbage of
                # editors...
                if template_file_name.startswith("."):
                    continue
                elif template_file_name.startswith("#"):
                    continue
                elif template_file_name.endswith("~"):
                    continue
                elif template_file_name.endswith(".bak"):
                    continue
                elif template_file_name.endswith(".xml.jinja2"):
                    continue
                elif template_file_name.endswith(".odx-cs"):
                    # we don't copy the comparam subset files (they
                    # are written based on the database)
                    continue

                template_file_mime_type = None
                if template_file_name.endswith(".odx-cs"):
                    template_file_mime_type = "application/x-asam.odx.odx-cs"
                elif template_file_name.endswith(".odx-d"):
                    template_file_mime_type = "application/x-asam.odx.odx-d"

                guessed_mime_type, guessed_encoding = mimetypes.guess_type(template_file_name)
                if template_file_mime_type is None and guessed_mime_type is not None:
                    template_file_mime_type = guessed_mime_type
                else:
                    template_file_mime_type = "application/octet-stream"

                in_path = [root]
                in_path.append(template_file_name)
                in_file_name = os.path.sep.join(in_path)

                template_file_stats = os.stat(in_file_name)
                template_file_cdate = datetime.datetime.fromtimestamp(template_file_stats.st_ctime)
                template_file_creation_date = template_file_cdate.strftime("%Y-%m-%dT%H:%M:%S")
                file_index.append(
                    (template_file_name, template_file_creation_date, template_file_mime_type))
                with zf.open(template_file_name, "w") as out_file:
                    out_file.write(open(in_file_name, "rb").read())

        # write the auxiliary files
        for output_file_name, data_file in database.auxiliary_files.items():
            file_cdate = datetime.datetime.fromtimestamp(time.time())
            creation_date = file_cdate.strftime("%Y-%m-%dT%H:%M:%S")

            mime_type = None
            if output_file_name.endswith(".odx-cs"):
                mime_type = "application/x-asam.odx.odx-cs"
            elif output_file_name.endswith(".odx-d"):
                mime_type = "application/x-asam.odx.odx-d"

            guessed_mime_type, guessed_encoding = mimetypes.guess_type(output_file_name)
            if mime_type is None and guessed_mime_type is not None:
                mime_type = guessed_mime_type
            else:
                mime_type = "application/octet-stream"

            zf_name = os.path.basename(output_file_name)
            with zf.open(zf_name, "w") as out_file:
                file_index.append((zf_name, creation_date, mime_type))
                out_file.write(data_file.read())

        jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(templates_dir))
        jinja_env.globals["getattr"] = getattr
        jinja_env.globals["hasattr"] = hasattr
        jinja_env.globals["odxraise"] = jinja2_odxraise_helper
        jinja_env.globals["make_xml_attrib"] = make_xml_attrib
        jinja_env.globals["make_bool_xml_attrib"] = make_bool_xml_attrib

        jinja_vars: dict[str, Any] = {}
        jinja_vars["odxtools_version"] = odxtools.__version__
        jinja_vars["database"] = database

        jinja_env.globals["set_category_docfrag"] = lambda cname, ctype: set_category_docfrag(
            jinja_vars, cname, ctype)
        jinja_env.globals["set_layer_docfrag"] = lambda lname: set_layer_docfrag(jinja_vars, lname)
        jinja_env.globals["make_ref_attribs"] = lambda ref: make_ref_attribs(jinja_vars, ref)

        # write the communication parameter subsets
        comparam_subset_tpl = jinja_env.get_template("comparam-subset.odx-cs.xml.jinja2")
        for comparam_subset in database.comparam_subsets:
            zf_file_name = f"{comparam_subset.short_name}.odx-cs"
            zf_file_cdate = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            zf_mime_type = "application/x-asam.odx.odx-cs"

            jinja_vars["comparam_subset"] = comparam_subset

            file_index.append((zf_file_name, zf_file_cdate, zf_mime_type))

            zf.writestr(zf_file_name, comparam_subset_tpl.render(**jinja_vars))

            del jinja_vars["comparam_subset"]

        # write the communication parameter specs
        comparam_spec_tpl = jinja_env.get_template("comparam-spec.odx-c.xml.jinja2")
        for comparam_spec in database.comparam_specs:
            zf_file_name = f"{comparam_spec.short_name}.odx-c"
            zf_file_cdate = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            zf_mime_type = "application/x-asam.odx.odx-c"

            jinja_vars["comparam_spec"] = comparam_spec

            file_index.append((zf_file_name, zf_file_cdate, zf_mime_type))

            zf.writestr(zf_file_name, comparam_spec_tpl.render(**jinja_vars))

            del jinja_vars["comparam_spec"]

        # write the actual diagnostic data.
        dlc_tpl = jinja_env.get_template("diag_layer_container.odx-d.xml.jinja2")
        for dlc in database.diag_layer_containers:
            jinja_vars["dlc"] = dlc

            file_name = f"{dlc.short_name}.odx-d"
            file_cdate = datetime.datetime.now()
            creation_date = file_cdate.strftime("%Y-%m-%dT%H:%M:%S")
            mime_type = "application/x-asam.odx.odx-d"

            file_index.append((file_name, creation_date, mime_type))
            zf.writestr(file_name, dlc_tpl.render(**jinja_vars))
            del jinja_vars["dlc"]

        # write the flash description objects
        flash_tpl = jinja_env.get_template("flash.odx-f.xml.jinja2")
        for flash in database.flashs:
            zf_file_name = f"{flash.short_name}.odx-f"
            zf_file_cdate = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            zf_mime_type = "application/x-asam.odx.odx-f"

            jinja_vars["flash"] = flash

            file_index.append((zf_file_name, zf_file_cdate, zf_mime_type))

            zf.writestr(zf_file_name, flash_tpl.render(**jinja_vars))

            del jinja_vars["flash"]

        # write the ECU-config objects
        ecu_config_tpl = jinja_env.get_template("ecu_config.odx-e.xml.jinja2")
        for ecu_config in database.ecu_configs:
            zf_file_name = f"{ecu_config.short_name}.odx-e"
            zf_file_cdate = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            zf_mime_type = "application/x-asam.odx.odx-e"

            jinja_vars["ecu_config"] = ecu_config

            file_index.append((zf_file_name, zf_file_cdate, zf_mime_type))

            zf.writestr(zf_file_name, ecu_config_tpl.render(**jinja_vars))

            del jinja_vars["ecu_config"]

        # write the index.xml file
        jinja_vars["file_index"] = file_index
        index_tpl = jinja_env.get_template("index.xml.jinja2")
        text = index_tpl.render(**jinja_vars)
        zf.writestr("index.xml", text)

    return True
