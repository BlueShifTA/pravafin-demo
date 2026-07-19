"""Core configuration and shared utilities.

Re-exported for cross-package use: `import coresat.core as csc` -> csc.get_settings().
"""

from .config import (
    Settings as Settings,
)
from .config import (
    get_settings as get_settings,
)
from .observability import (
    setup_logging as setup_logging,
)
from .observability import (
    with_runtime_logging as with_runtime_logging,
)
