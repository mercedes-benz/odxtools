# SPDX-License-Identifier: MIT
from enum import Enum
from typing import NewType

InheritancePriority = NewType("InheritancePriority", float)


class DiagLayerType(Enum):
    PROTOCOL = "PROTOCOL"
    FUNCTIONAL_GROUP = "FUNCTIONAL-GROUP"
    BASE_VARIANT = "BASE-VARIANT"
    ECU_VARIANT = "ECU-VARIANT"
    ECU_SHARED_DATA = "ECU-SHARED-DATA"

    @property
    def inheritance_priority(self) -> InheritancePriority:
        """Return the inheritance priority of diag layers of the given type

        ODX mandates that diagnostic layers can only inherit from
        layers of lower priority...

        """

        PRIORITY_OF_DIAG_LAYER_TYPE: dict[DiagLayerType, InheritancePriority] = {
            DiagLayerType.ECU_SHARED_DATA: InheritancePriority(0),
            DiagLayerType.PROTOCOL: InheritancePriority(1),
            DiagLayerType.FUNCTIONAL_GROUP: InheritancePriority(2),
            DiagLayerType.BASE_VARIANT: InheritancePriority(3),
            DiagLayerType.ECU_VARIANT: InheritancePriority(4),
        }

        return PRIORITY_OF_DIAG_LAYER_TYPE[self]
