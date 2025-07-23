from dataclasses import dataclass
from typing import TYPE_CHECKING

from packaging.version import Version

if TYPE_CHECKING:
    from odxtools.odxlink import OdxDocFragment


@dataclass(slots=True, frozen=True)
class OdxDocContext:
    version: Version

    # the doc_fragments are either tuple(doc_frag(category),)
    # or tuple(doc_frag(category), doc_frag(diag_layer))
    doc_fragments: tuple["OdxDocFragment"] | tuple["OdxDocFragment", "OdxDocFragment"]
