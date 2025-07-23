from dataclasses import dataclass
from xml.etree import ElementTree

from .odxdoccontext import OdxDocContext
from .utils import strip_indent


@dataclass(kw_only=True)
class Text:
    text: str
    text_identifier: str | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Text":
        # Extract the contents of the tag as a string.
        raw_string = et_element.text or ""
        for e in et_element:
            raw_string += ElementTree.tostring(e, encoding="unicode")

        text = strip_indent(raw_string)
        text_identifier = et_element.get("TI")

        return Text(text=text, text_identifier=text_identifier)

    @staticmethod
    def from_string(text: str) -> "Text":
        return Text(text=text, text_identifier=None)

    def __str__(self) -> str:
        return self.text
