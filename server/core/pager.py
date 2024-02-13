from typing import Optional

from utils.ints import IntUtils


class Pager:
    DEFAULT_PAGE = 1
    DEFAULT_LIMIT = 20

    page = DEFAULT_PAGE
    limit = DEFAULT_LIMIT
    total = 0

    _offset = None
    _query = None

    def set_page(self, page, default=DEFAULT_PAGE, minimum=1, maximum=None) -> 'Pager':
        self.page = self._sanitize(
            value=page,
            default=default,
            minimum=minimum,
            maximum=maximum
        )
        return self

    def reset_page(self) -> 'Pager':
        self.page = None
        return self

    def set_offset(self, offset, default=0, minimum=0, maximum=None) -> 'Pager':
        self._offset = self._sanitize(
            value=offset,
            default=default,
            minimum=minimum,
            maximum=maximum
        )
        return self

    def reset_offset(self) -> 'Pager':
        self._offset = None
        return self

    def set_total(self, total) -> 'Pager':
        self.total = total or 0
        return self

    def set_limit(self, limit, default=DEFAULT_LIMIT, minimum=1, maximum=1000) -> 'Pager':
        self.limit = self._sanitize(
            value=limit,
            default=default,
            minimum=minimum,
            maximum=maximum
        )
        return self

    def reset_limit(self) -> 'Pager':
        self.limit = None
        return self

    @classmethod
    def _sanitize(cls, value, default, minimum, maximum) -> int:
        value = IntUtils.to_int(value)
        if value:
            if isinstance(minimum, int) and minimum > value:
                return minimum
            elif isinstance(maximum, int) and maximum < value:
                return maximum
            else:
                return value
        else:
            return default

    @property
    def offset(self) -> int:
        if self._offset is None:
            if self.page and self.limit:
                self._offset = (self.page - 1) * self.limit
            else:
                return 0
        return self._offset

    def as_query(self) -> Optional[str]:
        if self._query is None:
            offset, limit = self.offset, self.limit
            if isinstance(offset, int) and limit:
                self._query = f'LIMIT {limit} OFFSET {offset}'
        return self._query or ''

    def dict(self) -> dict:
        if self.page and self.limit:
            return {
                'page': self.page,
                'offset': self.offset,
                'limit': self.limit,
                'total': self.total,
                'from_item_count': self.from_item_count(self.page, self.limit),
                'to_item_count': self.to_item_count(self.page, self.limit, self.total),
                'next_page': self.next_page(self.page, self.limit, self.total),
                'prev_page': self.prev_page(self.page),
            }
        return {}

    @classmethod
    def next_page(cls, page, limit, total) -> int:
        return page + 1 if page * limit < total else None

    @classmethod
    def prev_page(cls, page) -> int:
        return page - 1 if page > 1 else None

    @classmethod
    def to_item_count(cls, limit, page, total) -> int:
        count = limit * page
        return count if count <= total else total

    @classmethod
    def from_item_count(cls, page, limit) -> int:
        return (page - 1) * limit + 1
