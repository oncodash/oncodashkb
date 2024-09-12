import sys
from typing import TypeAlias
from typing import Optional
from enum import Enum
from enum import auto

import ontoweaver

# Allow accessing all ontoweaver.Item classes defined in this module.
all = ontoweaver.All(sys.modules[__name__])
