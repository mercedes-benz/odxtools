# SPDX-License-Identifier: MIT

from .compuconst import CompuConst

# make CompuInverseValue an alias for CompuConst. The XSD defines two
# separate but identical groups for this (why?)...
CompuInverseValue = CompuConst
