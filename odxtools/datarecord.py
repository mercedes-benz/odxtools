# SPDX-License-Identifier: MIT
import re
from dataclasses import dataclass, field
from typing import Any, cast
from xml.etree import ElementTree

from bincopy import BinFile

from .datafile import Datafile
from .dataformatselection import DataformatSelection
from .element import NamedElement
from .exceptions import odxraise, odxrequire
from .identvalue import IdentValue
from .odxdoccontext import OdxDocContext
from .odxlink import OdxLinkDatabase, OdxLinkId
from .snrefcontext import SnRefContext
from .specialdatagroup import SpecialDataGroup
from .utils import dataclass_fields_asdict


@dataclass(kw_only=True)
class DataRecord(NamedElement):
    rule: str | None = None
    key: str | None = None
    data_id: IdentValue | None = None
    sdgs: list[SpecialDataGroup] = field(default_factory=list)

    # at most one of the following two attributes is not None
    datafile: Datafile | None = None
    data: str | None = None

    dataformat: DataformatSelection

    @property
    def dataset(self) -> BinFile | bytearray:
        if self.datafile is not None:
            db = odxrequire(self._database)
            if db is None:
                return bytearray()

            datafile = odxrequire(self.datafile)
            if datafile is None:
                return bytearray()

            aux_file = odxrequire(db.auxiliary_files.get(datafile.value))
            if aux_file is None:
                return bytearray()

            data_str = aux_file.read().decode()
            aux_file.seek(0)
        elif self.data is not None:
            data_str = self.data
        else:
            odxraise("No data specified for DATA-RECORD")
            return bytearray()

        if self.dataformat in (DataformatSelection.INTEL_HEX, DataformatSelection.MOTOROLA_S):
            bf = BinFile()

            # remove white space and empty lines
            bf.add("\n".join([re.sub(r"\s", "", x) for x in data_str.splitlines() if x.strip()]))

            return bf
        elif self.dataformat == DataformatSelection.BINARY:
            return bytearray.fromhex(re.sub(r"\s", "", data_str, flags=re.MULTILINE))

        # user defined formats are not possible here
        odxraise(f"Unsupported data format {self.dataformat.value}")
        return bytearray()

    @property
    def blob(self) -> bytearray:
        """Computes the binary data blob that ought to be send to the ECU.

        i.e., this property stitches together the data of all
        segments.

        Note that, in order to reduce memory usage, this property is
        not computed when instanting the data record object, but at
        run time when it is accessed.
        """

        if isinstance(self.dataset, BinFile):
            return cast(bytearray, self.dataset.as_binary())

        return self.dataset

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "DataRecord":

        kwargs = dataclass_fields_asdict(NamedElement.from_et(et_element, context))

        rule = et_element.findtext("RULE")
        key = et_element.findtext("KEY")
        data_id = None
        if (did_elem := et_element.find("DATA-ID")) is not None:
            data_id = IdentValue.from_et(did_elem, context)
        sdgs = [SpecialDataGroup.from_et(sdge, context) for sdge in et_element.iterfind("SDGS/SDG")]
        datafile = None
        if (df_elem := et_element.find("DATA-FILE")) is not None:
            datafile = Datafile.from_et(df_elem, context)
        data = et_element.findtext("DATA")

        dataformat_str = odxrequire(et_element.attrib.get("DATAFORMAT"))
        try:
            dataformat = DataformatSelection(dataformat_str)
        except ValueError:
            dataformat = cast(DataformatSelection, None)
            odxraise(f"Encountered unknown data format selection '{dataformat_str}'")

        return DataRecord(
            rule=rule,
            key=key,
            data_id=data_id,
            sdgs=sdgs,
            datafile=datafile,
            data=data,
            dataformat=dataformat,
            **kwargs)

    def _build_odxlinks(self) -> dict[OdxLinkId, Any]:
        odxlinks: dict[OdxLinkId, Any] = {}

        return odxlinks

    def _resolve_odxlinks(self, odxlinks: OdxLinkDatabase) -> None:
        pass

    def _resolve_snrefs(self, context: SnRefContext) -> None:
        # this is slightly hacky because we only remember the
        # applicable ODX database and do not resolve any SNREFs here
        self._database = odxrequire(context.database)
