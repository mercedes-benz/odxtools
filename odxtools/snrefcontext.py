# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from .database import Database
    from .diaglayers.diaglayer import DiagLayer
    from .diagservice import DiagService
    from .parameters.parameter import Parameter
    from .request import Request
    from .response import Response
    from .singleecujob import SingleEcuJob
    from .statechart import StateChart


@dataclass
class SnRefContext:
    """Represents the context for which a short name reference ought
    to be resolved
    """

    database: Optional["Database"] = None
    diag_layer: Optional["DiagLayer"] = None
    diag_service: Optional["DiagService"] = None
    single_ecu_job: Optional["SingleEcuJob"] = None
    request: Optional["Request"] = None
    response: Optional["Response"] = None
    parameters: Optional[List["Parameter"]] = None
    state_chart: Optional["StateChart"] = None
