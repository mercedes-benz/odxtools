# SPDX-License-Identifier: MIT
from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .database import Database
    from .diaglayers.diaglayer import DiagLayer
    from .diagservice import DiagService
    from .multipleecujob import MultipleEcuJob
    from .parameters.parameter import Parameter
    from .request import Request
    from .response import Response
    from .singleecujob import SingleEcuJob
    from .statechart import StateChart


@dataclass(kw_only=True)
class SnRefContext:
    """Represents the context for which a short name reference ought
    to be resolved
    """

    database: Optional["Database"] = None
    diag_layer: Optional["DiagLayer"] = None
    diag_service: Optional["DiagService"] = None
    single_ecu_job: Optional["SingleEcuJob"] = None
    multiple_ecu_job: Optional["MultipleEcuJob"] = None
    request: Optional["Request"] = None
    response: Optional["Response"] = None
    parameters: list["Parameter"] | None = None
    state_chart: Optional["StateChart"] = None
