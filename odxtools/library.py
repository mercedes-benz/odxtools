# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast
from xml.etree import ElementTree

from .element import IdentifiableElement
from .exceptions import odxraise, odxrequire
from .odxlink import OdxDocFragment, OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .utils import dataclass_fields_asdict


@dataclass
class Library(IdentifiableElement):
    """
    A library defines a shared library used for single ECU jobs etc.

    It this is basically equivalent to ProgCode.
    """

    code_file: str
    encryption: Optional[str]
    syntax: str
    revision: str
    entrypoint: Optional[str]

    @property
    def code(self) -> bytes:
        return self._code

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "Library":

        kwargs = dataclass_fields_asdict(IdentifiableElement.from_et(et_element, doc_frags))

        code_file = odxrequire(et_element.findtext("CODE-FILE"))
        encryption = et_element.findtext("ENCRYPTION")
        syntax = odxrequire(et_element.findtext("SYNTAX"))
        revision = odxrequire(et_element.findtext("REVISION"))
        entrypoint = et_element.findtext("ENTRYPOINT")

        return Library(
            code_file=code_file,
            encryption=encryption,
            syntax=syntax,
            revision=revision,
            entrypoint=entrypoint,
            **kwargs)

    def _build_odxlinks(self) -> Dict[OdxLinkId, Any]:
        return {self.odx_id: self}

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
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
