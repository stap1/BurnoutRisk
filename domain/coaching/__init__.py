"""CoachPlanGenerator, TrendDetector i reguły coachingu (Faza 4)."""

from domain.coaching.actions import (
    DOZWOLONE_BUDZETY,
    OBSZARY_DZIALAN,
    CoachAction,
    CoachActionLibrary,
)
from domain.coaching.plan import (
    BASE_THRESHOLD,
    PLAN_DAYS,
    SAFETY_NOTE,
    CoachPlan,
    CoachPlanGenerator,
    PlannedAction,
)
from domain.coaching.trend import (
    SOFT_SUGGESTION,
    CheckinPoint,
    TrendConfig,
    TrendDetector,
    TrendResult,
)

__all__ = [
    "CoachAction",
    "CoachActionLibrary",
    "OBSZARY_DZIALAN",
    "DOZWOLONE_BUDZETY",
    "CoachPlan",
    "PlannedAction",
    "CoachPlanGenerator",
    "PLAN_DAYS",
    "BASE_THRESHOLD",
    "SAFETY_NOTE",
    "TrendDetector",
    "TrendConfig",
    "CheckinPoint",
    "TrendResult",
    "SOFT_SUGGESTION",
]
