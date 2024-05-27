from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from .exceptions import odxrequire
from .odxlink import OdxDocFragment


@dataclass
class Description:
    text: str
    external_docs: List[str]
    text_identifier: Optional[str]

    @staticmethod
    def from_et(et_element: Optional[ElementTree.Element],
                doc_frags: List[OdxDocFragment]) -> Optional["Description"]:
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

        text_identifier = et_element.get("TI")

        external_docs = \
            [
                odxrequire(ed.get("HREF")) for ed in et_element.iterfind("EXTERNAL-DOCS/EXTERNAL-DOC")
            ]
        return Description(text=text, text_identifier=text_identifier, external_docs=external_docs)

    @staticmethod
    def from_string(text: str) -> "Description":
        return Description(text=text, external_docs=[], text_identifier=None)

    def __str__(self) -> str:
        return self.text
