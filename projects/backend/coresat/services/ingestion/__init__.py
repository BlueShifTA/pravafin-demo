"""Ingestion pipeline: adapters parse, contracts validate, loaders publish.

Re-exported for cross-package use: `import coresat.services.ingestion as csi`.
"""

from .adapters import (
    DailyPricesCsvAdapter as DailyPricesCsvAdapter,
)
from .adapters import (
    FundamentalsCsvAdapter as FundamentalsCsvAdapter,
)
from .adapters import (
    FundsCsvAdapter as FundsCsvAdapter,
)
from .adapters import (
    ISharesHoldingsCsvAdapter as ISharesHoldingsCsvAdapter,
)
from .adapters import (
    PdfAdapter as PdfAdapter,
)
from .adapters import (
    UniverseCsvAdapter as UniverseCsvAdapter,
)
from .pipeline import (
    IngestionPipeline as IngestionPipeline,
)
from .pipeline import (
    build_registry as build_registry,
)
from .seed import merge_fundamentals as merge_fundamentals
