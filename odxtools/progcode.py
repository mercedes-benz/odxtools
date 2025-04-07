# SPDX-License-Identifier: MIT
from dataclasses import dataclass, field
from typing import Any, cast
from xml.etree import ElementTree

from .exceptions import odxraise, odxrequire
from .library import Library
from .nameditemlist import NamedItemList
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId, OdxLinkRef
from .snrefcontext import SnRefContext


@dataclass(kw_only=True)
class ProgCode:
    """A reference to code that is executed by a single ECU job"""
    code_file: str
    encryption: str | None = None
    syntax: str
    revision: str
    entrypoint: str | None = None
    library_refs: list[OdxLinkRef] = field(default_factory=list)

    @property
    def code(self) -> bytes:
        return self._code

    @property
    def libraries(self) -> NamedItemList[Library]:
        return self._libraries

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "ProgCode":
        code_file = odxrequire(et_element.findtext("CODE-FILE"))
        encryption = et_element.findtext("ENCRYPTION")
        syntax = odxrequire(et_element.findtext("SYNTAX"))
        revision = odxrequire(et_element.findtext("REVISION"))
        entrypoint = et_element.findtext("ENTRYPOINT")

        library_refs = [
            odxrequire(OdxLinkRef.from_et(el, context))
            for el in et_element.iterfind("LIBRARY-REFS/LIBRARY-REF")
        ]

        return ProgCode(
            code_file=code_file,
            encryption=encryption,
            syntax=syntax,
            revision=revision,
            entrypoint=entrypoint,
            library_refs=library_refs,
        )

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        return {}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        self._libraries = NamedItemList([odxlinks.resolve(x, Library) for x in self.library_refs])

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        aux_file = odxrequire(context.database).auxiliary_files.get(self.code_file)

        if aux_file is None:
            odxraise(f"Reference to auxiliary file '{self.code_file}' "
                     f"could not be resolved")
            self._code: bytes = cast(bytes, None)
            return

        self._code = aux_file.read()
        aux_file.seek(0)
