from typing import Optional


class IntUtils:

    @staticmethod
    def to_int(value, default=None) -> Optional[int]:
        if isinstance(value, int):
            return value
        elif isinstance(value, str):
            if value.isdigit():
                return int(value)
            elif value.startswith('-') and value[1:].isdigit():
                return int(value)
        if isinstance(default, int):
            return default
        return None

    @staticmethod
    def to_bool(value) -> bool:
        value = IntUtils.to_int(value)
        return True if isinstance(value, int) and value == 1 else False