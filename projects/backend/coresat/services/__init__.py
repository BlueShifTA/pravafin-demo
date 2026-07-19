"""Business logic services.

Re-exported for cross-package use: `import coresat.services as css`.
"""

from .analysis import AnalysisService as AnalysisService
from .analytics import AnalyticsService as AnalyticsService
from .comparison import ComparisonService as ComparisonService
from .example import echo_message as echo_message
from .grounding import (
    FabricatedNumberError as FabricatedNumberError,
)
from .grounding import (
    numbers_grounded as numbers_grounded,
)
from .grounding import (
    render_facts as render_facts,
)
from .indicators import (
    ema_series as ema_series,
)
from .indicators import (
    indicator_points as indicator_points,
)
from .indicators import (
    macd_series as macd_series,
)
from .indicators import (
    rsi_series as rsi_series,
)
from .indicators import (
    sma_series as sma_series,
)
from .portfolios import (
    PortfolioService as PortfolioService,
)
from .portfolios import (
    UnknownTickerError as UnknownTickerError,
)
from .projection import project as project
