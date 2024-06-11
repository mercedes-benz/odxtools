# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast
from xml.etree import ElementTree

from .exceptions import odxraise, odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext


@dataclass
class ProgCode:
    """A reference to code that is executed by a single ECU job"""
    code_file: str
    syntax: str
    revision: str
    encryption: Optional[str]
    entrypoint: Optional[str]
    library_refs: List[OdxLinkRef]

    @property
    def code(self) -> bytes:
        return self._code

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "ProgCode":
        code_file = odxrequire(et_element.findtext("CODE-FILE"))

        encryption = et_element.findtext("ENCRYPTION")
        syntax = odxrequire(et_element.findtext("SYNTAX"))
        revision = odxrequire(et_element.findtext("REVISION"))
        entrypoint = et_element.findtext("ENTRYPOINT")

        library_refs = [
            odxrequire(OdxLinkRef.from_et(el, doc_frags))
            for el in et_element.iterfind("LIBRARY-REFS/LIBRARY-REF")
        ]

        return ProgCode(
            code_file=code_file,
            syntax=syntax,
            revision=revision,
            encryption=encryption,
            entrypoint=entrypoint,
            library_refs=library_refs,
        )

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        # TODO: Libraries are currently not internalized.
        #       Once they are internalized, resolve the `library_refs` references here.
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        aux_file = odxrequire(context.database).auxiliary_files.get(self.code_file)

        if aux_file is None:
            odxraise(f"Reference to auxiliary file '{self.code_file}' "
                     f"could not be resolved")
            self._code: bytes = cast(bytes, None)
            return

        self._code = aux_file.read()
        aux_file.seek(0)
