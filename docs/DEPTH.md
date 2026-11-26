# 业务模块与回归证据

AI/ML / 传统ML · 中型

## 功能模块

| 编号 | 业务模块 | 交付内容 | 核心文件 | 测试文件 |
| --- | --- | --- | --- | --- |
| M1 | `collection_tickets` | 验签、换版与隔离 | `src/organichaul/collection_tickets/contracts.py` `src/organichaul/collection_tickets/parsing.py` `src/organichaul/collection_tickets/service.py` | `tests/test_collection_tickets.py` |
| M2 | `weighing_vintages` | 按可见时点冻结样本和结果 | `src/organichaul/weighing_vintages/contracts.py` `src/organichaul/weighing_vintages/revisions.py` `src/organichaul/weighing_vintages/service.py` | `tests/test_weighing_vintages.py` |
| M3 | `canteen_load` | 形成训练与当班共用的领域特征 | `src/organichaul/canteen_load/contracts.py` `src/organichaul/canteen_load/indicators.py` `src/organichaul/canteen_load/service.py` | `tests/test_canteen_load.py` |
| M4 | `haul_quantile` | 估计业务结果并输出本地归因 | `src/organichaul/haul_quantile/contracts.py` `src/organichaul/haul_quantile/estimator.py` `src/organichaul/haul_quantile/service.py` | `tests/test_haul_quantile.py` |
| M5 | `scale_backcheck` | 逐窗校准并与历史基线比较 | `src/organichaul/scale_backcheck/contracts.py` `src/organichaul/scale_backcheck/calibration.py` `src/organichaul/scale_backcheck/bands.py` `src/organichaul/scale_backcheck/service.py` | `tests/test_scale_backcheck.py` `tests/test_error_band.py` |
| M6 | `route_drift` | 识别缺测、未建档与分布变动 | `src/organichaul/route_drift/contracts.py` `src/organichaul/route_drift/distribution.py` `src/organichaul/route_drift/service.py` | `tests/test_route_drift.py` |
| M7 | `truck_capacity` | 按业务规则锁定和分派资源 | `src/organichaul/truck_capacity/contracts.py` `src/organichaul/truck_capacity/domain.py` `src/organichaul/truck_capacity/service.py` | `tests/test_truck_capacity.py` |
| M8 | `haul_manifest` | 按版本发布、导出、回查与对账 | `src/organichaul/haul_manifest/contracts.py` `src/organichaul/haul_manifest/storage.py` `src/organichaul/haul_manifest/service.py` | `tests/test_haul_manifest.py` |

## 高风险边界

| 编号 | 可观察后果 | 处理位置 | 回归用例 |
| --- | --- | --- | --- |
| TRAP-14 | 同版互斥读数隔离后继续处理其他单据 | `src/organichaul/weighing_vintages/service.py` | `tests/test_weighing_vintages.py::test_exact_resends_and_conflicts` |
| TRAP-19 | 单据锁定优先于排队和默认动作 | `src/organichaul/truck_capacity/service.py` | `tests/test_truck_capacity.py::test_locked_cannot_book` |
| TRAP-23 | 可见日等于截止的单据属于下一个窗口 | `src/organichaul/weighing_vintages/service.py` | `tests/test_weighing_vintages.py::test_at_cut_is_future` |
| TRAP-26 | 陈旧发布请求保留已生效的派工版 | `src/organichaul/haul_manifest/service.py` | `tests/test_haul_manifest.py::test_stale_leaves_head` |
| TRAP-32 | 恒定训练轴避免除零和新偏移误放 | `src/organichaul/canteen_load/service.py` | `tests/test_canteen_load.py::test_constant_axis` |
| TRAP-42 | 未来修订绝不替换前序训练证据 | `src/organichaul/weighing_vintages/service.py` | `tests/test_weighing_vintages.py::test_late_revision_cannot_revise_past` |
| TRAP-43 | 回放没有正例时说明指标不可定义 | `src/organichaul/scale_backcheck/service.py` | `tests/test_scale_backcheck.py::test_no_positive_average_precision` |
| TRAP-44 | 未建档片区会拒识，异常流量高时禁止发布 | `src/organichaul/route_drift/service.py` | `tests/test_route_drift.py::test_unseen_blocks_when_majority` |
| TRAP-53 | 批中相邻样本不改变单条评分 | `src/organichaul/haul_quantile/service.py` | `tests/test_haul_quantile.py::test_point_invariance` |
| TRAP-54 | 账簿参数变化会改变模型摘要并重算 | `src/organichaul/haul_quantile/service.py` | `tests/test_haul_quantile.py::test_fitted_signature_tracks_source` |
| TRAP-55 | 借来的误差带在本片区回放达不到覆盖目标即拒用，点位转人工 | `src/organichaul/scale_backcheck/bands.py` | `tests/test_error_band.py::test_borrowed_band_rejected_when_replay_falls_short` |
| TRAP-56 | 排车按可信上界占载，超出单车承载退回调度分批 | `src/organichaul/truck_capacity/domain.py` | `tests/test_error_band.py::test_upper_bound_over_capacity_returns_to_dispatch` |
| TRAP-57 | 迟到的称重修订不进入已冻结的校准或回放 | `src/organichaul/weighing_vintages/service.py` | `tests/test_error_band.py::test_late_revision_cannot_enter_closed_replay` |
