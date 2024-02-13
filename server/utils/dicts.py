import traceback
from typing import Optional


class DictUtils:

    @staticmethod
    def as_dict(value) -> Optional[dict]:
        return value if value and isinstance(value, dict) else None

    @staticmethod
    def to_dict(value) -> Optional[dict]:
        try:
            return dict(value)
        except Exception as e:
            print(e)
            traceback.print_exc()
        return None

    @staticmethod
    def validate_dict(
            value,
            is_strict: bool = False,  # Lenient/strict validation
            is_nullable: bool = False  # Allow/disallow nullable values
    ) -> Optional[dict]:
        if not value:
            return None
        if value and isinstance(value, dict):
            output_dict = {}
            for k, v in value.items():
                if not is_nullable:
                    if v is None:
                        continue

                if isinstance(v, int):
                    output_dict[k] = v
                elif isinstance(v, bool):
                    output_dict[k] = v
                elif isinstance(v, str):
                    trimmed = v.strip()
                    if is_nullable:
                        output_dict[k] = v
                    else:
                        if trimmed:
                            if is_strict:
                                if trimmed.isdigit():
                                    output_dict[k] = int(trimmed)
                                else:
                                    output_dict[k] = trimmed
                            else:
                                output_dict[k] = trimmed
                elif isinstance(v, tuple):
                    if is_nullable:
                        output_dict[k] = None
                    else:
                        if v:
                            output_dict[k] = v
                elif isinstance(v, set):
                    if is_nullable:
                        output_dict[k] = None
                    else:
                        if v:
                            output_dict[k] = v
                elif isinstance(v, list):
                    if is_nullable:
                        output_dict[k] = None
                    else:
                        if v:
                            output_dict[k] = v
                elif isinstance(v, dict):
                    if is_nullable:
                        output_dict[k] = None
                    else:
                        if v:
                            if is_strict:
                                output_dict[k] = DictUtils.validate_dict(v)
                            else:
                                output_dict[k] = v
                else:
                    output_dict[k] = v
            return output_dict if output_dict else None
        return None
