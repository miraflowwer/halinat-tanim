"""Resolution of user harvest dates to configured future periods."""

from datetime import date

from .config import EngineConfig
from .models import PlanningPeriod


class EngineInputError(ValueError):
    """A user input cannot be used by the engine."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def parse_iso_date(value: date | str, field_name: str) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise EngineInputError(
            "INVALID_DATE",
            f"{field_name} must be a valid ISO date in YYYY-MM-DD format.",
        ) from None


def resolve_supported_period(
    harvest_start: date | str,
    harvest_end: date | str,
    config: EngineConfig,
) -> tuple[date, date, PlanningPeriod]:
    """Resolve both requested dates to exactly one configured period."""
    start = parse_iso_date(harvest_start, "harvest_start")
    end = parse_iso_date(harvest_end, "harvest_end")
    if end < start:
        raise EngineInputError(
            "INVALID_DATE_RANGE",
            "harvest_end cannot be before harvest_start.",
        )

    containing = [
        period
        for period in config.future_periods
        if period.start <= start <= period.end and period.start <= end <= period.end
    ]
    if len(containing) == 1:
        return start, end, containing[0]

    start_periods = [
        period for period in config.future_periods if period.start <= start <= period.end
    ]
    end_periods = [
        period for period in config.future_periods if period.start <= end <= period.end
    ]
    if start_periods and end_periods and start_periods[0] != end_periods[0]:
        raise EngineInputError(
            "HARVEST_PERIOD_SPANS_MULTIPLE_PERIODS",
            "The harvest period crosses more than one supported planning period.",
        )
    raise EngineInputError(
        "UNSUPPORTED_HARVEST_PERIOD",
        "The harvest period is outside the configured future planning horizon.",
    )
