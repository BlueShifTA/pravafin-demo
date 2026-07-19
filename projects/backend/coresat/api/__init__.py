"""API routers for the backend.

Re-exported for cross-package use: `import coresat.api as capi` -> capi.market_router.
Each module exposes `router`, so they are re-exported under distinct names.
"""

from .analysis import router as analysis_router
from .chat import (
    info_router as copilot_info_router,
)
from .chat import (
    router as chat_router,
)
from .compare import router as compare_router
from .draft import router as draft_router
from .example import router as example_router
from .health import router as health_router
from .ingest import router as ingest_router
from .market import router as market_router
from .portfolios import router as portfolios_router

__all__ = [
    "analysis_router",
    "chat_router",
    "compare_router",
    "copilot_info_router",
    "draft_router",
    "example_router",
    "health_router",
    "ingest_router",
    "market_router",
    "portfolios_router",
]
