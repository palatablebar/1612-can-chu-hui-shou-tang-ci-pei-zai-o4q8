from collections import defaultdict
from dataclasses import dataclass

from .contracts import ValidationPoint

SHARED_TARGET = .82          # 共用误差带的原有覆盖目标
MIN_REPLAY_EVIDENCE = 8      # 判定借用是否成立所需的最少本片区回放称重


@dataclass(frozen=True, slots=True)
class ErrorBand:
    """一个片区对共用误差带的可用性判定。radius 为 None 表示无可信带。"""

    region: str
    radius: float | None
    source: str
    weighings: int
    replay_samples: int
    replay_coverage: float | None
    trusted: bool
    reason: str

    def rows(self) -> dict:
        return {'region': self.region, 'source': self.source, 'radius': self.radius,
                'weighings': self.weighings, 'replay_samples': self.replay_samples,
                'replay_coverage': self.replay_coverage, 'trusted': self.trusted,
                'reason': self.reason}


def coverage(points: list[ValidationPoint], radius: float) -> float | None:
    matured = [row for row in points if row.confirmed]
    if not matured:
        return None
    return sum(abs(row.estimate-row.observed) <= radius for row in matured) / len(matured)


def resolve_bands(calibration: list[ValidationPoint], holdout: list[ValidationPoint],
                  shared_radius: float, *, target: float = SHARED_TARGET,
                  min_evidence: int = MIN_REPLAY_EVIDENCE) -> tuple[ErrorBand, ...]:
    """共用一条误差带；逐片区检验借用在回放中是否仍达到原有覆盖目标。"""
    weighed: dict[str, int] = defaultdict(int)
    for row in calibration:
        if row.confirmed:
            weighed[row.region] += 1
    replay: dict[str, list[ValidationPoint]] = defaultdict(list)
    for row in holdout:
        replay[row.region].append(row)

    bands = []
    for region in sorted(set(weighed) | set(replay)):
        samples = [row for row in replay[region] if row.confirmed]
        measured = coverage(replay[region], shared_radius)
        if weighed[region] == 0:
            bands.append(ErrorBand(region, None, '共用误差带', 0, len(samples), measured, False,
                                   '本片区没有校准期称重，无法确认借用误差带可信'))
        elif not samples:
            bands.append(ErrorBand(region, None, '共用误差带', weighed[region], 0, None, False,
                                   '本片区没有回放称重可供验证，误差带不可借用'))
        elif len(samples) < min_evidence:
            bands.append(ErrorBand(region, None, '共用误差带', weighed[region], len(samples), measured, False,
                                   f'本片区回放称重仅 {len(samples)} 条，不足以验证借用误差带'))
        elif measured < target:
            bands.append(ErrorBand(region, None, '共用误差带', weighed[region], len(samples), measured, False,
                                   f'借用的误差带在本片区回放覆盖 {measured:.3f}，未达到 {target:.2f} 目标'))
        else:
            bands.append(ErrorBand(region, shared_radius, '共用误差带', weighed[region], len(samples), measured,
                                   True, '借用共用误差带，本片区回放覆盖达标'))
    return tuple(bands)


def withheld(bands: tuple[ErrorBand, ...], region: str) -> ErrorBand:
    """该片区没有校准称重时，共用误差带一律不可借用。"""
    for band in bands:
        if band.region == region:
            return band
    return ErrorBand(region, None, '共用误差带', 0, 0, None, False,
                     '本片区没有校准期称重，无法确认借用误差带可信')
