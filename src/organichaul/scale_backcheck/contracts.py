from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .bands import ErrorBand


@dataclass(frozen=True, slots=True)
class ValidationPoint:
    key: str
    region: str
    day: int
    estimate: float
    observed: float
    confirmed: bool


@dataclass(frozen=True, slots=True)
class Block:
    end: float
    count: int
    positive: float

    @property
    def fraction(self) -> float:
        return self.positive / self.count


@dataclass(frozen=True, slots=True)
class Adjustment:
    name: str
    buckets: tuple[Block, ...]
    radius: float
    samples: int
    native_scale: bool

    def apply(self, value: float) -> float:
        if not self.buckets:
            return value
        previous = None
        for current in self.buckets:
            if value <= current.end:
                if previous is None or current.end <= previous.end:
                    return current.fraction
                weight = (value - previous.end) / (current.end - previous.end)
                return (1-weight)*previous.fraction + weight*current.fraction
            previous = current
        return self.buckets[-1].fraction

    def interval(self, prediction: float, radius: float | None = None) -> tuple[float, float]:
        reach = self.radius if radius is None else radius
        threshold = prediction + reach
        if not self.native_scale:
            threshold = min(1., threshold)
        return max(0., prediction - reach), threshold


@dataclass(frozen=True, slots=True)
class Validation:
    adjustment: Adjustment
    holdout_metrics: dict
    regions: dict
    excluded: tuple[tuple[str, int], ...]
    points: tuple[ValidationPoint, ...]
    bands: tuple['ErrorBand', ...] = ()

    def band(self, region: str) -> 'ErrorBand | None':
        for row in self.bands:
            if row.region == region:
                return row
        return None

    def report(self) -> dict:
        return {'adjustment': self.adjustment.name, 'calibration_count': self.adjustment.samples,
                'radius': self.adjustment.radius,
                'calibration_blocks': [{'through': b.end, 'risk': b.fraction, 'weight': b.count}
                                       for b in self.adjustment.buckets],
                'holdout': self.holdout_metrics, 'regions': self.regions,
                'excluded': dict(self.excluded),
                'bands': [row.rows() for row in self.bands],
                'unbanded_regions': [row.region for row in self.bands if not row.trusted]}
