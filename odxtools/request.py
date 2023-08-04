# SPDX-License-Identifier: MIT
from .basicstructure import BasicStructure


class Request(BasicStructure):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"Request('{self.short_name}')"

    def __str__(self) -> str:
        return f"Request('{self.short_name}')"
