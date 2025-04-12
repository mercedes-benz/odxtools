# SPDX-License-Identifier: MIT
from enum import Enum
from typing import NewType

TInheritancePrio = NewType("TInheritancePrio", float)


class DiagLayerType(Enum):
    PROTOCOL = "PROTOCOL"
    FUNCTIONAL_GROUP = "FUNCTIONAL-GROUP"
    BASE_VARIANT = "BASE-VARIANT"
    ECU_VARIANT = "ECU-VARIANT"
    ECU_SHARED_DATA = "ECU-SHARED-DATA"

    @property
    def inheritance_priority(self) -> TInheritancePrio:
        """Return the inheritance priority of diag layers of the given type

        ODX mandates that diagnostic layers can only inherit from
        layers of lower priority...

        """

        PRIORITY_OF_DIAG_LAYER_TYPE: dict[DiagLayerType, TInheritancePrio] = {
            DiagLayerType.ECU_SHARED_DATA: TInheritancePrio(0),
            DiagLayerType.PROTOCOL: TInheritancePrio(1),
            DiagLayerType.FUNCTIONAL_GROUP: TInheritancePrio(2),
            DiagLayerType.BASE_VARIANT: TInheritancePrio(3),
            DiagLayerType.ECU_VARIANT: TInheritancePrio(4),
        }

        return PRIORITY_OF_DIAG_LAYER_TYPE[self]
