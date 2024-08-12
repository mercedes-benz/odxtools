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
            DiagLayerType.PROTOCOL:
                1,
            DiagLayerType.FUNCTIONAL_GROUP:
                2,
            DiagLayerType.BASE_VARIANT:
                3,
            DiagLayerType.ECU_VARIANT:
                4,

            # ECU shared data layers are a bit weird (see section
            # 7.3.2.4.4 of the ASAM specification): they can be
            # inherited from by any other layer but they will
            # override any objects which are also provided by any of
            # the other parent layers. tl;dr: When it comes to
            # inheritance, they have the highest priority.
            DiagLayerType.ECU_SHARED_DATA:
                100,
        }

        return PRIORITY_OF_DIAG_LAYER_TYPE[self]
