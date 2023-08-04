# SPDX-License-Identifier: MIT
from enum import Enum
from typing import Dict


class DiagLayerType(Enum):
    PROTOCOL = "PROTOCOL"
    FUNCTIONAL_GROUP = "FUNCTIONAL-GROUP"
    BASE_VARIANT = "BASE-VARIANT"
    ECU_VARIANT = "ECU-VARIANT"
    ECU_SHARED_DATA = "ECU-SHARED-DATA"

    @property
    def inheritance_priority(self) -> int:
        """Return the inheritance priority of diag layers of the given type

        ODX mandates that diagnostic layers can only inherit from
        layers of lower priority...

        """

        PRIORITY_OF_DIAG_LAYER_TYPE: Dict[DiagLayerType, int] = {
            DiagLayerType.ECU_SHARED_DATA: 0,
            DiagLayerType.PROTOCOL: 1,
            DiagLayerType.FUNCTIONAL_GROUP: 2,
            DiagLayerType.BASE_VARIANT: 3,
            DiagLayerType.ECU_VARIANT: 4,
        }

        return PRIORITY_OF_DIAG_LAYER_TYPE[self]
