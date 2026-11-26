from math import ceil

from ..canteen_load.contracts import Prepared
from .contracts import Disposition, Draft

SINGLE_TRUCK_UNITS = 11  # 单车承载上限（车载百公斤）


def interpret(resolved: Prepared, value: float, uncertainty: float) -> Draft:
    probe = resolved.record

    def block(reason: str) -> Draft:
        return Draft(resolved,Disposition.MANUAL,0,0,1,0,0,reason,'')

    def normal(reason: str) -> Draft:
        return Draft(resolved,Disposition.NORMAL,0,0,1,0,0,reason,'')

    def proposal(qty: int, priority: float, minutes: int, reason: str, resource: str,
                 *, minimum: int | None = None, unit: int = 1) -> Draft:
        return Draft(resolved,Disposition.BOOKED,qty,qty if minimum is None else minimum,
                     unit,priority,minutes,reason,resource)

    covers, bins, hours, events, fill, road = resolved.raw
    if hours >= 32 and probe.window < 50:
        return block('暂存已近时限且现场交接不足五十分钟')
    floor_kilos = bins * fill * 0.27
    kilos = max(value + uncertainty, floor_kilos)
    tons = ceil(kilos / 100)
    if tons > SINGLE_TRUCK_UNITS:
        return block(f'点位可信上界 {kilos:.0f} 公斤超出单车承载，需拆趟分批清运')
    if tons < 3 and hours < 19:
        return normal('等待常规趟次，暂存仍有余量')
    servicing = ceil(road * 2.1 + bins * 1.9)
    return proposal(max(1, tons), hours * 2.7 + fill * .22 + kilos * .025, servicing,
                    '按可信上界重量与暂存时间占用车载额度', '路区车载')
