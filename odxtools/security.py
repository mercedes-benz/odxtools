# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from xml.etree import ElementTree

from .fwchecksum import FwChecksum
from .fwsignature import FwSignature
from .odxdoccontext import OdxDocContext
from .securitymethod import SecurityMethod
from .validityfor import ValidityFor


@dataclass(kw_only=True)
class Security:
    security_method: SecurityMethod | None = None
    fw_signature: FwSignature | None = None
    fw_checksum: FwChecksum | None = None
    validity_for: ValidityFor | None = None

    @staticmethod
    def from_et(et_element: ElementTree.Element, context: OdxDocContext) -> "Security":
        security_method = None
        if (sm_elem := et_element.find("SECURITY-METHOD")) is not None:
            security_method = SecurityMethod.from_et(sm_elem, context)

        fw_signature = None
        if (fws_elem := et_element.find("FW-SIGNATURE")) is not None:
            fw_signature = FwSignature.from_et(fws_elem, context)

        fw_checksum = None
        if (fwcs_elem := et_element.find("FW-CHECKSUM")) is not None:
            fw_checksum = FwChecksum.from_et(fwcs_elem, context)

        validity_for = None
        if (val_elem := et_element.find("VALIDITY-FOR")) is not None:
            validity_for = ValidityFor.from_et(val_elem, context)

        return Security(
            security_method=security_method,
            fw_signature=fw_signature,
            fw_checksum=fw_checksum,
            validity_for=validity_for,
        )
