# SPDX-License-Identifier: MIT
from dataclasses import dataclass

from .basicstructure import BasicStructure


@dataclass
class Request(BasicStructure):

    def __repr__(self) -> str:
        return f"Request('{self.short_name}')"

    def __str__(self) -> str:
        return f"Request('{self.short_name}')"
