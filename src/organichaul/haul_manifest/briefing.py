from collections import defaultdict
from math import isfinite, sqrt

from ..settings import EXPOSURE_UNIT, FIELDS


def reading(key: str, label: str, value: float, unit: str, trigger: float, direction: str) -> dict:
    number = float(value)
    boundary = float(trigger)
    if not isfinite(number) or not isfinite(boundary):
        raise ValueError(f'{label} 指标不是有限量')
    if direction not in ('high','low'):
        raise ValueError('证据边界方向不明')
    crossed = number > boundary if direction=='high' else number < boundary
    return {'field':key,'label':label,'value':round(number,3),'unit':unit,'trigger':round(boundary,3),
            'direction':direction,'exceeded':crossed}


def summarize(record: dict) -> dict:
    fields = record['raw']
    if any(fields[item.key] is None for item in FIELDS):
        return {'checks':[],'work':None,'exposure':None, 'work_label':None, 'status':'读数不全'}
    values = tuple(fields[item.key] for item in FIELDS)
    window = record['window']
    prediction = record.get('estimate')
    covers,bins,hours,events,fill,road = values
    kilos = max(float(prediction or 0),bins*fill*.27)
    full_bins = bins*fill/100
    per_stop_minutes = 2.1*road+1.9*bins
    findings = [
        reading('temperature_buffer','暂存剩余时间',36-hours,'小时',5,'low'),
        reading('loading_volume','预计载重',kilos,'公斤',1100,'high'),
        reading('bin_equivalents','满载桶折算',full_bins,'桶',19,'high'),
        reading('route_duration','单点行车及装载',per_stop_minutes,'分钟',window,'high')]
    work = min(kilos,100*record['units'])
    outcome = '点位估计已预留公斤'
    exposure = max(0,kilos-100*record['units']) if hours>=24 else 0
    return {'checks':findings,'work':round(work,3),'work_label':outcome,'exposure':round(exposure,3),'status':'可核算'}


def tally(rows: list[dict]) -> dict:
    by_region = defaultdict(lambda: {'measured':0,'missing':0,'work':0.,'exposure':0.,'outside':0})
    for row in rows:
        area = by_region[row['region']]
        note = row['business_evidence']
        if note['work'] is None:
            area['missing'] += 1
        else:
            area['measured'] += 1
            area['work'] += note['work']
            area['exposure'] += note['exposure']
            area['outside'] += sum(check['exceeded'] for check in note['checks'])
    aggregates = {'work':0.,'exposure':0.,'source_missing':0,'outside_count':0}
    for area in by_region.values():
        aggregates['work'] += area['work']
        aggregates['exposure'] += area['exposure']
        aggregates['source_missing'] += area['missing']
        aggregates['outside_count'] += area['outside']
    aggregates['work'] = round(aggregates['work'],3)
    aggregates['exposure'] = round(aggregates['exposure'],3)
    return {**aggregates,'exposure_unit':EXPOSURE_UNIT,'regions':dict(sorted(by_region.items()))}
