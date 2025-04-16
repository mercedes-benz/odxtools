from typing import TYPE_CHECKING, NamedTuple

from packaging.version import Version

if TYPE_CHECKING:
    from odxtools.odxlink import OdxDocFragment


class OdxDocContext(NamedTuple):
    version: Version
    doc_fragments: list["OdxDocFragment"]
