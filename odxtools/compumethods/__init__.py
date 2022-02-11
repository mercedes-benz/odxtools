# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

"""Subpackage containing all compu methods.

A computational method is used to convert the physical type
into the internal type and vice versa.

All compu methods inherit from the abstract base class CompuMethod.
Each category is represented by a different sub class.
"""

from .compumethodbase import CompuMethod
from .identicalcompumethod import IdenticalCompuMethod
from .linearcompumethod import LinearCompuMethod
from .scalelinearcompumethod import ScaleLinearCompuMethod
from .tabintpcompumethod import TabIntpCompuMethod
from .texttablecompumethod import TexttableCompuMethod

from .compurationalcoeffs import CompuRationalCoeffs
from .compuscale import CompuScale
from .limit import IntervalType, Limit
from .readcompumethod import read_compu_method_from_odx
