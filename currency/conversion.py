from typing import Optional


def convert(original_value: Optional[float], conversion_rate: float):
    if not original_value:
        return
    return round(original_value * conversion_rate, 3)
