from typing import TYPE_CHECKING, NamedTuple

from packaging.version import Version

if TYPE_CHECKING:
    from odxtools.odxlink import OdxDocFragment


class OdxDocContext(NamedTuple):
    version: Version

    # the doc_fragments are either tuple(category,) or tuple(category, diag_layer)
    doc_fragments: tuple["OdxDocFragment"] | tuple["OdxDocFragment", "OdxDocFragment"]
