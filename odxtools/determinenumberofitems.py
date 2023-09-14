from dataclasses import dataclass
from typing import List
from xml.etree import ElementTree

from .odxlink import OdxDocFragment
from .positioneddataobjectproperty import PositionedDataObjectProperty
from .utils import dataclass_fields_asdict


@dataclass
class DetermineNumberOfItems(PositionedDataObjectProperty):

    @staticmethod
    def from_et(et_element: ElementTree.Element,
                doc_frags: List[OdxDocFragment]) -> "DetermineNumberOfItems":
        kwargs = dataclass_fields_asdict(
            PositionedDataObjectProperty.from_et(et_element, doc_frags))
        return DetermineNumberOfItems(**kwargs)
