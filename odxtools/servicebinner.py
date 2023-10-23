# SPDX-License-Identifier: MIT
from io import StringIO
from typing import Dict, Iterable, Iterator, Optional

from . import obd, uds
from .diagservice import DiagService
from .nameditemlist import NamedItemList
from .parameters.codedconstparameter import CodedConstParameter


class ServiceBinner:
    """Class to categorize a long list of services into the service
    groups defined by the UDS or OBD standards.

    This class is supposed to be used like this:

    db = odxtools.load_file("my_cool_diagnostics_db.pdx")
    ...
    service_groups = ServiceBinner(db.ecus.my_ecu.services)
    print(service_groups)
    """

    def __init__(self, services: Iterable[DiagService]):
        service_groups: Dict[Optional[int], NamedItemList[DiagService]] = {}
        for service in services:
            SID = self.__extract_sid(service)

            if SID not in service_groups:
                service_groups[SID] = NamedItemList()

            service_groups[SID].append(service)

        self._service_groups = service_groups

    def __extract_sid(self, service: DiagService) -> Optional[int]:
        # diagnostic services without requests are possible; just like
        # aircraft without wings...
        if service.request is None:
            return None

        prefix = 0  # prefix of constant parameters
        cursor = 0  # bit position of the next parameter
        for param in service.request.parameters:
            if not isinstance(param, CodedConstParameter):
                # we *need* at least the first byte of a request to be statically defined!
                return None

            param_len = param.get_static_bit_length()
            if param_len is None:
                return None

            if not isinstance(param.coded_value, int):
                return None

            prefix <<= param_len
            prefix |= param.coded_value & ((1 << param_len) - 1)
            cursor += param_len

            if cursor >= 8:
                # we have a prefix that is at least 8 bits
                # long. return its most significant byte.
                prefix >>= cursor - 8
                return prefix & 0xff

        return None

    def __str__(self) -> str:
        """Return an informative string about which of the diagnostic
        services are part of which UDS or OBD service group.

        """
        result = StringIO()
        for sid, service_list in self._service_groups.items():
            if isinstance(sid, int):
                sid_name = obd.sid_to_name(sid)
                if sid_name is not None:
                    print(f"OBD service group '{sid_name}' (0x{sid:x}):", file=result)
                elif (sid_name := uds.sid_to_name(sid)) is not None:
                    print(f"UDS service group '{sid_name}' (0x{sid:x}):", file=result)
                else:
                    print(f"Unknown service group 0x{sid:x}:", file=result)
            else:
                print(f"Non-standard services:", file=result)
            for service in service_list:
                print(f"  {service.short_name}", file=result)

        return result.getvalue()

    def __repr__(self) -> str:
        """Return an string representing the object
        """
        result = StringIO()
        result.write("[ ")
        result.write(", ".join([f"0x{x}" for x in self._service_groups if x is not None]))
        result.write(" ]")

        return result.getvalue()

    def __iter__(self) -> Iterator[Optional[int]]:
        return iter(self._service_groups)

    def __getitem__(self, sid: Optional[int]) -> NamedItemList[DiagService]:
        if sid is None:
            return self._service_groups.get(sid, NamedItemList())

        if sid < 0 or sid > 255:
            raise IndexError(f"SIDs must be in range 0x00 to 0xff")

        return self._service_groups.get(sid, NamedItemList())
