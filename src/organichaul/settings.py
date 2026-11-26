from .collection_tickets.contracts import Field

EXPOSURE_UNIT = '超时点位未配载公斤'
TITLE = '餐厨回收趟次配载'
ROLE = '餐厨回收车队调度'
OBJECT = '清运点单'
TARGET = '次日称重公斤'
ALGORITHM = '分位回归（Pinball 损失）'
MODE = 'regression'
IS_SURVIVAL = False
MODEL_EPOCH = 'organichaul-1.0'
REGIONS = ('南市场', '西街区', '产业园')
SIGNAL_NAMES = ('per_bin_service', 'stored_fill', 'meal_mix', 'pickup_age', 'detour_weight')
RAW_EXPLAIN_INDEX = (None, None, None, None, None)
RESOURCE = '车载百公斤'
DEFAULT_BUDGET = 75
ACTION = '预留清运车'
MANUAL_ACTION = '核对暂存交接'
NORMAL_ACTION = '正常路线'
WORKFLOW = '未称重时按保守预测占载，超过车辆承载的点位拆回调度。'
PLACEMENT_MODE = 'early_run'
POOL_LIMIT = 3
SEPARATE_CONTEXTS = False
HAS_WORKBENCH = False
SAMPLE_NAME = 'organichaul_register.csv'

FIELDS = (
    Field('covers', '预订餐位', '位', 45, 560, True),
    Field('bins', '暂存桶', '桶', 2, 28, True),
    Field('hours', '距上次清运', '小时', 6, 39, False),
    Field('events', '团餐份数', '份', 0, 250, True),
    Field('fill', '桶满度', '%', 15, 98, False),
    Field('road', '往返里程', '公里', 2, 38, False),
)
