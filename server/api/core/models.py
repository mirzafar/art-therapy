import uuid
from datetime import datetime
from hashlib import md5
from typing import Optional, List

from pydantic import BaseModel, validator, ValidationError

from core.db import mongo


# class Example(BaseModel):
#     name: str = None
#     signup_ts: Optional[datetime] = None
#     friends: List[int] = []



