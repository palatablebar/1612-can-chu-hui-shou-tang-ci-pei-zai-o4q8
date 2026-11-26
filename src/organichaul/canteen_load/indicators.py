def derive(values: tuple[float, ...]) -> tuple[float, ...]:
    """从清运点单原始读数生成五个模型轴。"""
    covers, bins, hours, events, fill, road = values
    bin_occupancy = bins * fill / 100
    meal_equivalent = covers + events * 1.42
    productive_hours = hours * (1 + min(20.0, hours) / 66)
    scale_sensitive = 0.36 * meal_equivalent + 16.0 * bin_occupancy
    return meal_equivalent / bins, bin_occupancy, meal_equivalent, productive_hours, scale_sensitive / (1 + road / 56)
