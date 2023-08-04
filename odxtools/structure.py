# SPDX-License-Identifier: MIT
from .basicstructure import BasicStructure


class Structure(BasicStructure):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"Structure('{self.short_name}', byte_size={self.byte_size})"

    def __str__(self) -> str:
        params = ("[\n" + "\n".join([" " + str(p).replace("\n", "\n ") for p in self.parameters]) +
                  "\n]")

        return (f"Structure '{self.short_name}': " + f"Byte size={self.byte_size}, " +
                f"Parameters={params}")
