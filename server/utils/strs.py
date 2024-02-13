from typing import Optional


class StrUtils:

    @staticmethod
    def to_str(value, default='') -> Optional[str]:
        if isinstance(value, int) or isinstance(value, float):
            return str(value)
        elif value and isinstance(value, str):
            output = value.strip()
            return output if output else None
        elif value and isinstance(value, bytes):
            return str(value)
        if isinstance(default, str):
            return default
        return None

    @staticmethod
    def to_bool(value) -> bool:
        value = StrUtils.to_str(value)
        return True if value and value.lower() == 'true' else False

    @staticmethod
    def uncapitalize(value) -> Optional[str]:
        if not value:
            return None
        if value:
            value = value[0].lower() + value[1:]
        return value

    @staticmethod
    def replace_first(value, char, predicate: bool) -> Optional[str]:
        if not value:
            return None
        if predicate and isinstance(predicate, bool):
            if not char:
                return None
            if char != value[0]:
                return char + value[1:]
        return value
