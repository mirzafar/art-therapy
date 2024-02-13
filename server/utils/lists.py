from typing import List, Optional

from utils.dicts import DictUtils
from utils.ints import IntUtils
from utils.strs import StrUtils


class ListUtils:

    @staticmethod
    def to_list(value):
        if value and isinstance(value, list):
            return value
        return None

    @staticmethod
    def distinct(value) -> Optional[list]:
        if value and isinstance(value, list):
            return list(set(value))
        return None

    @staticmethod
    def append(elements, item) -> Optional[list]:
        if elements and isinstance(elements, list):
            if item not in elements:
                elements.append(item)
        return elements

    @staticmethod
    def remove(elements, item) -> Optional[list]:
        if elements and isinstance(elements, list):
            if item in elements:
                elements.remove(item)
        return elements

    @staticmethod
    def to_list_of_ints(value, distinct=False) -> List[int]:
        if value and isinstance(value, list):
            output = []
            for item in value:
                converted = IntUtils.to_int(item)
                if isinstance(converted, int):
                    if distinct:
                        if converted in output:
                            continue
                    output.append(converted)
            return output if output else []
        return []

    @staticmethod
    def to_list_of_strs(value, distinct=False) -> Optional[List[str]]:
        if value and isinstance(value, list):
            output = []
            for item in value:
                converted = StrUtils.to_str(item)
                if converted:
                    if distinct:
                        if converted in output:
                            continue
                    output.append(converted)
            return output if output else None
        return None

    @staticmethod
    def to_list_of_dicts(value, clean=False) -> List[dict]:
        output = []
        if value and isinstance(value, list):
            for item in value:
                if clean:
                    output.append(DictUtils.validate_dict(dict(item)))
                else:
                    output.append(dict(item))
        return output

    @staticmethod
    def depth(value) -> int:
        if value and isinstance(value, list):
            return 1 + max(ListUtils.depth(item) for item in value)
        return 0
