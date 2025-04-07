from dataclasses import dataclass, field
from typing import Optional
from xml.etree import ElementTree

from .exceptions import odxrequire
from .externaldoc import ExternalDoc
from .odxdoccontext import OdxDocContext


@dataclass(kw_only=True)
class Description:
    text: str
    external_docs: list[ExternalDoc] = field(default_factory=list)

    text_identifier: str | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element | None,
                context: OdxDocContext) -> Optional["Description"]:
        if et_element is None:
            return None

        # Extract the contents of the tag as a XHTML string.
        raw_string = et_element.text or ""
        for e in et_element:
            if e.tag == "EXTERNAL-DOCS":
                break
            raw_string += ElementTree.tostring(e, encoding="unicode")

        # remove white spaces at the beginning and at the end of all
        # extracted lines
        stripped_lines = [x.strip() for x in raw_string.split("\n")]

        text = "\n".join(stripped_lines).strip()

        external_docs = \
            [
                odxrequire(ExternalDoc.from_et(ed, context)) for ed in et_element.iterfind("EXTERNAL-DOCS/EXTERNAL-DOC")
            ]

        text_identifier = et_element.attrib.get("TI")

        return Description(text=text, text_identifier=text_identifier, external_docs=external_docs)

    @staticmethod
    def from_string(text: str) -> "Description":
        return Description(text=text, external_docs=[], text_identifier=None)

    def __str__(self) -> str:
        return self.text
