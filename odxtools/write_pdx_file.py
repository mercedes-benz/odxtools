# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

import zipfile
import os
import odxtools
import jinja2
import time
import datetime
import inspect

from typing import Any, Dict, List, Tuple

from .exceptions import OdxError
from .comparam_subset import BaseComparam

odxdatabase = None

def jinja2_odxraise_helper(msg: str) -> None:
    raise Exception(msg)

def comparam_subset_name(x: BaseComparam) -> str:
    """Find the short name of the comparam subset which contains a
    given communication parameter"""
    global odxdatabase

    assert odxdatabase is not None

    for cps in odxdatabase.comparam_subsets:
        for cp in cps.comparams:
            if cp.short_name == x.short_name:
                return cps.short_name

    raise OdxError(f"Communication parameter {x.short_name} is not defined.")

__module_filename = inspect.getsourcefile(odxtools)
assert isinstance(__module_filename, str)
__pdx_stub_dir = os.path.sep.join([os.path.dirname(__module_filename),
                                  "pdx_stub"])
def write_pdx_file(output_file_name : str,
                   database : odxtools.Database,
                   auxiliary_content_specifiers : List[Tuple[str, bytes]] = [],
                   stub_dir : str = __pdx_stub_dir) -> bool:
    """
    Write an internalized database to a PDX file.
    """
    global odxdatabase

    odxdatabase = database

    file_index = list()
    with zipfile.ZipFile(output_file_name,
                         mode="w",
                         compression=zipfile.ZIP_DEFLATED) as zf:

        # write all files in the stub directory
        for root, dir, files in os.walk(stub_dir):
            for stub_file_name in files:
                # we are not interested in the autosave garbage of
                # editors...
                if stub_file_name.startswith("."):
                    continue
                elif stub_file_name.startswith("#"):
                    continue
                elif stub_file_name.endswith("~"):
                    continue
                elif stub_file_name.endswith(".bak"):
                    continue
                elif stub_file_name.endswith(".tpl"):
                    continue
                elif stub_file_name.endswith(".odx-cs"):
                    # we don't copy the comparam subset files (they
                    # are written based on the database)
                    continue

                stub_file_mime_type = "text/plain"
                if stub_file_name.endswith(".odx-cs"):
                    stub_file_mime_type = "application/x-asam.odx.odx-cs"
                elif stub_file_name.endswith(".odx-d"):
                    stub_file_mime_type = "application/x-asam.odx.odx-d"

                in_path = list([root])
                in_path.append(stub_file_name)
                in_file_name = os.path.sep.join(in_path)

                stub_file_stats = os.stat(in_file_name)
                stub_file_cdate = datetime.datetime.fromtimestamp(stub_file_stats.st_ctime)
                stub_file_creation_date = stub_file_cdate.strftime("%Y-%m-%dT%H:%M:%S")
                file_index.append( (stub_file_name,
                                    stub_file_creation_date,
                                    stub_file_mime_type) )
                with zf.open(stub_file_name, "w") as out_file:
                    out_file.write(open(in_file_name, "rb").read())

        # write the auxiliary files
        for output_file_name, data in auxiliary_content_specifiers:
            file_cdate = datetime.datetime.fromtimestamp(time.time())
            creation_date = file_cdate.strftime("%Y-%m-%dT%H:%M:%S")

            mime_type = "text/plain"
            if stub_file_name.endswith(".odx-cs"):
                mime_type = "application/x-asam.odx.odx-cs"
            elif stub_file_name.endswith(".odx-d"):
                mime_type = "application/x-asam.odx.odx-d"

            zf_name = os.path.basename(output_file_name)
            with zf.open(zf_name, "w") as out_file:
                file_index.append( (zf_name, creation_date, mime_type) )
                out_file.write(data)  # type: ignore

        jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(stub_dir))
        jinja_env.globals['hasattr'] = hasattr
        jinja_env.globals['odxraise'] = jinja2_odxraise_helper
        jinja_env.globals['comparam_subset_name'] = comparam_subset_name

        # allows to put XML attributes on a separate line while it is
        # collapsed with the previous line in the rendering
        jinja_env.filters["odxtools_collapse_xml_attribute"] = lambda x: " "+x.strip() if x.strip() else ""

        vars: Dict[str, Any] = {}
        vars["odxtools_version"] = odxtools.__version__
        vars["database"] = database

        # write the communication parameter subsets
        comparam_subset_tpl = jinja_env.get_template("comparam-subset.odx-cs.tpl")
        for comparam_subset in database.comparam_subsets:
            zf_file_name = f"{comparam_subset.short_name}.odx-cs"
            zf_file_cdate = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            zf_mime_type = "application/x-asam.odx.odx-cs"

            vars["comparam_subset"] = comparam_subset

            file_index.append( (zf_file_name,
                                zf_file_cdate,
                                zf_mime_type) )

            zf.writestr(zf_file_name, comparam_subset_tpl.render(**vars))
        del vars["comparam_subset"]

        # write the actual diagnostic data.
        dlc_tpl = jinja_env.get_template("diag_layer_container.odx-d.tpl")
        for dlc in database.diag_layer_containers:
            vars["dlc"] = dlc

            file_name = f"{dlc.short_name}.odx-d"
            file_cdate = datetime.datetime.now()
            creation_date = file_cdate.strftime("%Y-%m-%dT%H:%M:%S")
            mime_type = "application/x-asam.odx.odx-d"

            file_index.append( (file_name, creation_date, mime_type) )
            zf.writestr(file_name, dlc_tpl.render(**vars))
        del vars["dlc"]

        # write the index.xml file
        vars["file_index"] = file_index
        index_tpl = jinja_env.get_template("index.xml.tpl")
        text = index_tpl.render(**vars)
        zf.writestr("index.xml", text)

    return True
