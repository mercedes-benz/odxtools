# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, cast
from xml.etree import ElementTree

from .exceptions import odxraise, odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId, OdxLinkRef

if TYPE_CHECKING:
    from .diaglayer import DiagLayer


class ProgCodeSyntax(Enum):
    JAVA = "JAVA"
    CLASS = "CLASS"
    JAR = "JAR"


@dataclass
class ProgCode:
    """A reference to code that is executed by a single ECU job"""
    code_file: str
    syntax: ProgCodeSyntax
    revision: str
    encryption: Optional[str]
    entrypoint: Optional[str]
    library_refs: List[OdxLinkRef]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "ProgCode":
        code_file = odxrequire(et_element.findtext("CODE-FILE"))

        encryption = et_element.findtext("ENCRYPTION")

        syntax_str = odxrequire(et_element.findtext("SYNTAX"))
        try:
            syntax = ProgCodeSyntax(syntax_str)
        except ValueError:
            syntax = cast(ProgCodeSyntax, None)
            odxraise(f"Encountered unknown program code syntax '{syntax_str}'")

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

    def _resolve_snrefs(self, diag_layer: "DiagLayer") -> None:
        pass
