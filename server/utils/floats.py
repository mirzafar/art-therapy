from typing import Optional


class FloatUtils:

    @staticmethod
    def to_float(value, default=None) -> Optional[float]:
        if isinstance(value, float):
            return value
        elif isinstance(value, str):
            if value.replace('.', '').isdigit():
                return float(value)
            elif value.startswith('-') and value[1:].replace('.', '').isdigit():
                return float(value)
        if isinstance(default, float):
            return default
        return None

    @staticmethod
    def format_percentage(value) -> Optional[float]:
        if isinstance(value, int) or isinstance(value, float):
            return float('{:.1f}'.format(value))
        return None
