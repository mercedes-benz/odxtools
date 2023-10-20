# SPDX-License-Identifier: MIT
from io import StringIO
from typing import Dict, Iterable, Optional

from .diagservice import DiagService
from .nameditemlist import NamedItemList
from .parameters.codedconstparameter import CodedConstParameter


class UdsBinner:
    """Class to categorize a long list of services into the service
    groups defined by the UDS standard.

    This class is supposed to be used like this:

    db = odxtools.load_file("my_cool_diagnostics_db.pdx")
    ...
    uds_bins = UdsBinner(db.ecus.my_ecu)
    print(uds_bins)
    """

    def __init__(self, services: Iterable[DiagService]):
        service_groups: Dict[Optional[int], NamedItemList[DiagService]] = {}
        for service in services:
            SID = self.__extract_sid(service)

            if SID not in service_groups:
                service_groups[SID] = NamedItemList()

            service_groups[SID].append(service)

        self.service_groups = service_groups

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
        services are part of which UDS service group.

        """
        result = StringIO()
        for sid, service_list in self.service_groups.items():
            sid_name = self.sid_to_name.get(sid)
            if isinstance(sid, int):
                if sid_name is not None:
                    print(f"UDS service group '{sid_name}' (0x{sid:x}):", file=result)
                else:
                    print(f"Non-standard UDS service group 0x{sid:x}:", file=result)
            else:
                print(f"Non standard services:", file=result)
            for service in service_list:
                print(f"  {service.short_name}", file=result)

        return result.getvalue()

    #: map from the ID of a service group to its human-readable name
    #: as defined by the UDS standard
    sid_to_name = {
        # diagnostic services that cannot be categorized in terms of
        # the UDS standard get `None` as their SID...
        None: "Not Applicable",
        0x10: "Session",
        0x11: "ECU Reset",
        0x27: "Security Access",
        0x28: "Communication Control",
        0x29: "Authentication",
        0x3e: "Tester Present",
        0x83: "Access Timing Parameter",
        0x84: "Secured Data Transmission",
        0x85: "Control DTC Settings",
        0x86: "Response On Event",
        0x87: "Link Control",
        0x22: "Read Data By Identifier ",
        0x23: "Read Memory By Address",
        0x24: "Read Scaling Data By Identifier",
        0x2a: "Read Data By Periodic Identifier",
        0x2c: "Dynamically Define Data Identifier",
        0x2e: "Write Data By Identifier",
        0x3d: "Write Memory By Address ",
        0x14: "Clear Diagnostic Information",
        0x19: "Read DTC Information",
        0x2f: "Input Output Control By Identifier",
        0x31: "Routine Control",
        0x34: "Request Download",
        0x35: "Request Upload",
        0x36: "Transfer Data",
        0x37: "Request Transfer Exit",
        0x38: "Request File Transfer",
    }

    def __getitem__(self, sid: Optional[int]) -> NamedItemList[DiagService]:
        if sid is None:
            return self.service_groups.get(sid, NamedItemList())

        if sid < 0 or sid > 255:
            raise IndexError(f"SIDs must be in range 0x00 to 0xff")

        return self.service_groups.get(sid, NamedItemList())
