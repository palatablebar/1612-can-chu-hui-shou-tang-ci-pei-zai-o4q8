from dataclasses import replace
from math import ceil

from organichaul.canteen_load.contracts import Prepared
from organichaul.collection_tickets.contracts import Hold, Ticket
from organichaul.scale_backcheck.bands import SHARED_TARGET, coverage, resolve_bands
from organichaul.scale_backcheck.contracts import ValidationPoint
from organichaul.truck_capacity.contracts import Disposition
from organichaul.truck_capacity.domain import interpret
from organichaul.truck_capacity.service import draft
from organichaul.weighing_vintages.contracts import Windows
from organichaul.weighing_vintages.service import split


def point(region, index, estimate, observed, confirmed=True):
    return ValidationPoint(f'{region}-{index}', region, 100+index, estimate, observed, confirmed)


def near(region, count, offset=10.0):
    """回放误差恒为 offset（在带内），可稳定达到覆盖目标。"""
    return [point(region, i, 500.0+i, 500.0+i+offset) for i in range(count)]


def far(region, count, offset=140.0):
    return [point(region, i, 500.0+i, 500.0+i+offset) for i in range(count)]


# 借用误差带：本片区回放覆盖不足时必须拒用
def test_borrowed_band_rejected_when_replay_falls_short():
    calibration = [*near('南市场', 30), *near('产业园', 30), *near('西街区', 30)]
    holdout = [*near('西街区', 18), *near('南市场', 18), *near('产业园', 18)]
    bands = {row.region: row for row in resolve_bands(calibration, holdout, 60.0)}

    assert bands['西街区'].trusted and bands['西街区'].radius == 60.0

    weak = [*near('南市场', 6), *far('南市场', 12)]
    bands = {row.region: row for row in resolve_bands(calibration, weak, 60.0)}
    assert bands['南市场'].trusted is False
    assert bands['南市场'].radius is None
    assert bands['南市场'].replay_coverage < SHARED_TARGET
    assert '未达到' in bands['南市场'].reason


def test_band_needs_enough_replay_weighings_before_borrowing():
    calibration = near('南市场', 30)
    bands = resolve_bands(calibration, near('南市场', 3), 60.0)
    row = bands[0]
    assert row.trusted is False and row.radius is None
    assert row.replay_coverage == 1.0
    assert '不足以验证' in row.reason


def test_band_never_borrowed_without_calibration_weighings():
    bands = resolve_bands([], far('新片区', 20), 60.0)
    row = bands[0]
    assert row.trusted is False and row.radius is None
    assert '没有校准期称重' in row.reason


def test_coverage_ignores_unmatured_points():
    mixed = [*near('南市场', 4), point('南市场', 9, 500.0, 999.0, confirmed=False)]
    assert coverage(mixed, 60.0) == 1.0


# 可信上界占载：误差带必须计入占用，而不是只按点预测
def ticket(bins=12.0, fill=70.0, hours=24.0, window=90, road=10.0):
    return Ticket('K-1', '西街区', 'ROUTE-1', 118, 118, 1, 600, window, Hold.CLEAR,
                  (300.0, bins, hours, 120.0, fill, road), None, None, None, False, 'live')


def prepared(**kwargs):
    return Prepared(ticket(**kwargs), (300.0, 12.0, 24.0, 120.0, 70.0, 10.0), (0.0,)*5, (0.0,)*5, (), (), 0.0)


def test_upper_bound_includes_error_band():
    signal = prepared()
    without_band = interpret(signal, 500.0, 0.0)
    with_band = interpret(signal, 500.0, 120.0)
    assert without_band.units == 5
    assert with_band.units == ceil(max(620.0, signal.raw[1]*signal.raw[4]*.27)/100) == 7
    assert '可信上界' in with_band.why


def test_upper_bound_over_capacity_returns_to_dispatch():
    signal = prepared()
    plan = interpret(signal, 500.0, 700.0)
    assert plan.units == 0
    assert plan.state == Disposition.MANUAL
    assert '拆趟' in plan.why


def test_missing_band_sends_point_to_manual():
    signal = prepared()
    plan = draft(signal, 500.0, None, '借用的误差带在本片区回放未达标')
    assert plan.state == Disposition.MANUAL and plan.units == 0
    assert '回放未达标' in plan.why
    kept = draft(signal, 500.0, 60.0)
    assert kept.state == Disposition.BOOKED and kept.units > 0


# 迟到称重不进已过截点的校准或回放
def test_late_revision_cannot_enter_closed_replay(source):
    original = next(item for item in source.tickets
                    if item.phase == 'history' and 93 <= item.day < 117
                    and item.complete and item.outcome_day is not None)
    late = replace(original, received=124, revision=2, target=original.target+50)
    vintage = split((*source.tickets, late), Windows())
    stored = next(item for item in vintage.holdout.evaluated if item.key == original.key)
    assert stored.revision == 1 and stored.target == original.target


def test_late_revision_cannot_enter_closed_calibration(source):
    original = next(item for item in source.tickets
                    if item.phase == 'history' and 66 <= item.day < 93
                    and item.complete and item.outcome_day is not None)
    late = replace(original, received=120, revision=2, target=original.target+50)
    vintage = split((*source.tickets, late), Windows())
    stored = next(item for item in vintage.calibration.evaluated if item.key == original.key)
    assert stored.revision == 1 and stored.target == original.target
