# SPDX-License-Identifier: MIT
from .validityfor import ValidityFor

# Note that the ODX specification specifies a separate tag for this,
# but this tag is identical to VALIDITY-FOR, so let's use a type alias
# to reduce the amount of copy-and-pasted code
FwSignature = ValidityFor
