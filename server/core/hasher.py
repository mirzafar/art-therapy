from hashlib import md5
from typing import Optional

from utils.strs import StrUtils


def password_to_hash(password) -> Optional[str]:
    password = StrUtils.to_str(password)

    if password:
        hasher = md5()
        hasher.update(password.encode())
        return hasher.hexdigest()
    else:
        return None
