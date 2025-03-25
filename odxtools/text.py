from dataclasses import dataclass
from typing import List, Optional
from xml.etree import ElementTree

from .odxlink import OdxDocFragment


@dataclass
class Text:
    text: str
    text_identifier: Optional[str]

    @staticmethod
    def from_et(et_element: ElementTree.Element, doc_frags: List[OdxDocFragment]) -> "Text":
        # Extract the contents of the tag as a string.
        raw_string = et_element.text or ""
        for e in et_element:
            raw_string += ElementTree.tostring(e, encoding="unicode")

        # remove white spaces at the beginning and at the end of all
        # extracted lines
        stripped_lines = [x.strip() for x in raw_string.split("\n")]

        text = "\n".join(stripped_lines).strip()

        text_identifier = et_element.get("TI")

        return Text(text=text, text_identifier=text_identifier)

    @staticmethod
    def from_string(text: str) -> "Text":
        return Text(text=text, text_identifier=None)

    def __str__(self) -> str:
        return self.text
