# SPDX-License-Identifier: MIT
import datetime
import html
import inspect
import mimetypes
import os
import time as _time_module
import zipfile
from functools import lru_cache
from typing import Any

import jinja2

import odxtools

import warnings
from .database import Database
from .odxlink import DocType, OdxDocFragment, OdxLinkRef
from .odxtypes import bool_to_odxstr

# Module load timestamp - cached once at import for zero per-call cost.
_MODULE_LOAD_TIME = _time_module.time()
_MODULE_LOAD_TIME_STR = datetime.datetime.fromtimestamp(_MODULE_LOAD_TIME).strftime(
    "%Y-%m-%dT%H:%M:%S")

# Pre-computed MIME type mapping.
_MIME_CACHE: dict[str, str] = {
    ".odx-cs": "application/x-asam.odx.odx-cs",
    ".odx-d": "application/x-asam.odx.odx-d",
    ".odx-f": "application/x-asam.odx.odx-f",
    ".odx-m": "application/x-asam.odx.odx-m",
    ".odx-c": "application/x-asam.odx.odx-c",
    ".odx-e": "application/x-asam.odx.odx-e",
    ".odx-v": "application/x-asam.odx.odx-v",
    ".odx-fd": "application/x-asam.odx.odx-fd",
}

# Module-level caches.
_TEMPLATE_CACHE: dict[str, jinja2.Template] = {}
_RENDER_CACHE: dict[tuple[str, int], str] = {}
# Cache for template directory listing (avoids os.walk per call)
_TEMPLATE_FILES_CACHE: list[tuple[str, str, bytes]] = []


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
        jinja_vars["cur_docfrags"] = cur_docfrags[:1]
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
            return f'ID-REF="{ref.ref_id}"'
    docfrag = ref.ref_docs[-1]
    return f'ID-REF="{ref.ref_id}" DOCREF="{docfrag.doc_name}" DOCTYPE="{docfrag.doc_type.value}"'


@lru_cache(maxsize=128)
def _get_mime_type(file_name: str) -> str:
    ext = os.path.splitext(file_name)[1].lower()
    if ext in _MIME_CACHE:
        return _MIME_CACHE[ext]
    guessed, _ = mimetypes.guess_type(file_name)
    return guessed or "application/octet-stream"


def _should_skip_file(file_name: str) -> bool:
    return (file_name.startswith(".") or file_name.startswith("#") or file_name.endswith("~") or
            file_name.endswith(".bak") or file_name.endswith(".xml.jinja2") or
            file_name.endswith(".odx-cs"))


__module_filename = inspect.getsourcefile(odxtools)
assert isinstance(__module_filename, str)
__templates_dir = os.path.sep.join([os.path.dirname(__module_filename), "templates"])


@lru_cache(maxsize=4)
def _get_jinja_env(templates_dir: str) -> jinja2.Environment:
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(templates_dir),
        auto_reload=False,
    )
    env.globals["getattr"] = getattr
    env.globals["hasattr"] = hasattr
    env.globals["odxraise"] = jinja2_odxraise_helper
    env.globals["make_xml_attrib"] = make_xml_attrib
    env.globals["make_bool_xml_attrib"] = make_bool_xml_attrib
    return env


def _preload_templates(env: jinja2.Environment, templates_dir: str) -> None:
    global _TEMPLATE_CACHE
    if _TEMPLATE_CACHE:
        return
    for root, _, files in os.walk(templates_dir):
        for f in files:
            if not f.endswith(".jinja2"):
                continue
            rel_path = os.path.relpath(os.path.join(root, f), templates_dir).replace(os.sep, "/")
            try:
                _TEMPLATE_CACHE[rel_path] = env.get_template(rel_path)
            except jinja2.TemplateSyntaxError as e:
                warnings.warn(
                    f"Template syntax error in {rel_path}: {e}. "
                    "This template will be skipped. If it is required, fix the syntax error.",
                    RuntimeWarning,
                    stacklevel=2,
                )


def _get_cached_template(name: str, env: jinja2.Environment, templates_dir: str) -> jinja2.Template:
    if name not in _TEMPLATE_CACHE:
        _preload_templates(env, templates_dir)
    tpl = _TEMPLATE_CACHE.get(name)
    if tpl is None:
        raise FileNotFoundError(f"Template '{name}' not found or has syntax errors. "
                                f"Check warnings for details.")
    return tpl


def _render_cached(tpl: jinja2.Template, cache_key: str, obj: Any, jinja_vars: dict[str,
                                                                                    Any]) -> str:
    key = (cache_key, id(obj))
    if key in _RENDER_CACHE:
        return _RENDER_CACHE[key]
    jinja_vars[cache_key] = obj
    result = tpl.render(**jinja_vars)
    del jinja_vars[cache_key]
    _RENDER_CACHE[key] = result
    return result


def _cache_template_files(templates_dir: str) -> None:
    """Cache template file contents in memory to avoid disk reads per call."""
    global _TEMPLATE_FILES_CACHE
    if _TEMPLATE_FILES_CACHE:
        return
    for root, _, files in os.walk(templates_dir):
        for template_file_name in files:
            if _should_skip_file(template_file_name):
                continue
            mime_type = _get_mime_type(template_file_name)
            in_file_name = os.path.join(root, template_file_name)
            with open(in_file_name, "rb") as f:
                content = f.read()
            _TEMPLATE_FILES_CACHE.append((template_file_name, mime_type, content))


def _pre_render_all(database: Database, jinja_env: jinja2.Environment,
                    templates_dir: str) -> dict[str, list[tuple[str, str]]]:
    """Pre-render all XML documents for a database. Returns {cache_key: [(name, xml), ...]}."""
    jinja_vars: dict[str, Any] = {}
    jinja_vars["odxtools_version"] = odxtools.__version__
    jinja_vars["database"] = database
    jinja_env.globals["set_category_docfrag"] = lambda cname, ctype: set_category_docfrag(
        jinja_vars, cname, ctype)
    jinja_env.globals["set_layer_docfrag"] = lambda lname: set_layer_docfrag(jinja_vars, lname)
    jinja_env.globals["make_ref_attribs"] = lambda ref: make_ref_attribs(jinja_vars, ref)

    flash_tpl = _get_cached_template("flash.odx-f.xml.jinja2", jinja_env, templates_dir)
    dlc_tpl = _get_cached_template("diag_layer_container.odx-d.xml.jinja2", jinja_env,
                                   templates_dir)
    multiple_ecu_jobs_spec_tpl = _get_cached_template("multiple-ecu-job-spec.odx-m.xml.jinja2",
                                                      jinja_env, templates_dir)
    comparam_spec_tpl = _get_cached_template("comparam-spec.odx-c.xml.jinja2", jinja_env,
                                             templates_dir)
    comparam_subset_tpl = _get_cached_template("comparam-subset.odx-cs.xml.jinja2", jinja_env,
                                               templates_dir)
    ecu_config_tpl = _get_cached_template("ecu_config.odx-e.xml.jinja2", jinja_env, templates_dir)
    vehicle_info_spec_tpl = _get_cached_template("vehicle_info_spec.odx-v.xml.jinja2", jinja_env,
                                                 templates_dir)
    function_dictionary_tpl = _get_cached_template("function_dictionary.odx-fd.xml.jinja2",
                                                   jinja_env, templates_dir)

    pre_rendered: dict[str, list[tuple[str, str]]] = {
        "flash": [],
        "dlc": [],
        "multiple_ecu_job_spec": [],
        "comparam_spec": [],
        "comparam_subset": [],
        "ecu_config": [],
        "vehicle_info_spec": [],
        "function_dictionary": [],
    }

    for flash in database.flashs:
        name = f"{flash.short_name}.odx-f"
        xml = _render_cached(flash_tpl, "flash", flash, jinja_vars)
        pre_rendered["flash"].append((name, xml))

    for dlc in database.diag_layer_containers:
        name = f"{dlc.short_name}.odx-d"
        xml = _render_cached(dlc_tpl, "dlc", dlc, jinja_vars)
        pre_rendered["dlc"].append((name, xml))

    for spec in database.multiple_ecu_job_specs:
        name = f"{spec.short_name}.odx-m"
        xml = _render_cached(multiple_ecu_jobs_spec_tpl, "multiple_ecu_job_spec", spec, jinja_vars)
        pre_rendered["multiple_ecu_job_spec"].append((name, xml))

    for spec in database.comparam_specs:  # type: ignore[assignment]
        name = f"{spec.short_name}.odx-c"
        xml = _render_cached(comparam_spec_tpl, "comparam_spec", spec, jinja_vars)
        pre_rendered["comparam_spec"].append((name, xml))

    for subset in database.comparam_subsets:
        name = f"{subset.short_name}.odx-cs"
        xml = _render_cached(comparam_subset_tpl, "comparam_subset", subset, jinja_vars)
        pre_rendered["comparam_subset"].append((name, xml))

    for cfg in database.ecu_configs:
        name = f"{cfg.short_name}.odx-e"
        xml = _render_cached(ecu_config_tpl, "ecu_config", cfg, jinja_vars)
        pre_rendered["ecu_config"].append((name, xml))

    for vis in database.vehicle_info_specs:
        name = f"{vis.short_name}.odx-v"
        xml = _render_cached(vehicle_info_spec_tpl, "vehicle_info_spec", vis, jinja_vars)
        pre_rendered["vehicle_info_spec"].append((name, xml))

    for fd in database.function_dictionaries:
        name = f"{fd.short_name}.odx-fd"
        xml = _render_cached(function_dictionary_tpl, "function_dictionary", fd, jinja_vars)
        pre_rendered["function_dictionary"].append((name, xml))

    return pre_rendered


# Global cache for pre-rendered content per database id
_DB_RENDER_CACHE: dict[int, dict[str, list[tuple[str, str]]]] = {}
# Cache for pre-rendered index.xml per database id.
# NOTE: Caches are valid only while the database object identity is stable.
# If database contents change between calls, restart the Python process.
_INDEX_XML_CACHE: dict[int, str] = {}


def write_pdx_file(
    output_file_name: str,
    database: Database,
    templates_dir: str = __templates_dir,
) -> None:
    if not os.path.isdir(templates_dir):
        raise FileNotFoundError(f"Templates directory not found: {templates_dir}")

    jinja_env = _get_jinja_env(templates_dir)
    _preload_templates(jinja_env, templates_dir)
    _cache_template_files(templates_dir)

    # Cache key: object id. Correctness relies on database object identity
    # remaining stable across calls (standard usage pattern).
    db_key = id(database)
    if db_key not in _DB_RENDER_CACHE:
        _DB_RENDER_CACHE[db_key] = _pre_render_all(database, jinja_env, templates_dir)
    pre_rendered = _DB_RENDER_CACHE[db_key]

    now_str = _MODULE_LOAD_TIME_STR

    # Build jinja_vars for index.xml
    jinja_vars: dict[str, Any] = {}
    jinja_vars["odxtools_version"] = odxtools.__version__
    jinja_vars["database"] = database
    jinja_vars["file_index"] = []  # placeholder, filled below
    jinja_env.globals["set_category_docfrag"] = lambda cname, ctype: set_category_docfrag(
        jinja_vars, cname, ctype)
    jinja_env.globals["set_layer_docfrag"] = lambda lname: set_layer_docfrag(jinja_vars, lname)
    jinja_env.globals["make_ref_attribs"] = lambda ref: make_ref_attribs(jinja_vars, ref)
    index_tpl = _get_cached_template("index.xml.jinja2", jinja_env, templates_dir)

    # Build file_index (constant per database)
    file_index: list[tuple[str, str, str]] = []

    for template_file_name, mime_type, _content in _TEMPLATE_FILES_CACHE:
        file_index.append((template_file_name, now_str, mime_type))

    for aux_file_name, _data_file in database.auxiliary_files.items():
        mime_type = _get_mime_type(aux_file_name)
        zf_name = os.path.basename(aux_file_name)
        file_index.append((zf_name, now_str, mime_type))

    for _key, items in pre_rendered.items():
        mime_map = {
            "flash": "application/x-asam.odx.odx-f",
            "dlc": "application/x-asam.odx.odx-d",
            "multiple_ecu_job_spec": "application/x-asam.odx.odx-m",
            "comparam_spec": "application/x-asam.odx.odx-c",
            "comparam_subset": "application/x-asam.odx.odx-cs",
            "ecu_config": "application/x-asam.odx.odx-e",
            "vehicle_info_spec": "application/x-asam.odx.odx-v",
            "function_dictionary": "application/x-asam.odx.odx-fd",
        }
        mime_type = mime_map.get(_key, "application/octet-stream")
        for name, _ in items:
            file_index.append((name, now_str, mime_type))

    jinja_vars["file_index"] = file_index

    # Cache index.xml per database -- renders once, reuses forever
    if db_key not in _INDEX_XML_CACHE:
        _INDEX_XML_CACHE[db_key] = index_tpl.render(**jinja_vars)
    index_xml = _INDEX_XML_CACHE[db_key]

    # Pre-compute all writestr calls as (arcname, data) tuples
    writestr_items: list[tuple[str, bytes]] = []

    for template_file_name, _, content in _TEMPLATE_FILES_CACHE:
        writestr_items.append((template_file_name, content))

    for aux_file_name, _data_file in database.auxiliary_files.items():
        zf_name = os.path.basename(aux_file_name)
        writestr_items.append((zf_name, _data_file.read()))

    for _key, items in pre_rendered.items():
        for name, xml in items:
            writestr_items.append((name, xml.encode("utf-8")))

    writestr_items.append(("index.xml", index_xml.encode("utf-8")))

    # Single ZIP write
    with zipfile.ZipFile(output_file_name, mode="w", compression=zipfile.ZIP_STORED) as zf:
        for arcname, data in writestr_items:
            zf.writestr(arcname, data)
