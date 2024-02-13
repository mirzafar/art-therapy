from typing import Optional

from utils.strs import StrUtils


class Sorter:
    request = None
    specs = None

    _query = None
    _mongo_query = None
    _elastic_query = None

    # Example: 'id:desc,title:asc'
    def set_request(self, request, default=None) -> 'Sorter':
        request = StrUtils.to_str(request)
        self.request = request if request else StrUtils.to_str(default)
        return self

    # Example: {'id': 'p.id', 'title': 'p.title'}
    def set_specs(self, specs) -> 'Sorter':
        if specs and isinstance(specs, dict):
            if all(
                isinstance(field, str) and isinstance(reference, str)
                for field, reference in specs.items()
            ):
                self.specs = specs
        return self

    # Example: {'position': 'p.position'}
    def update_specs(self, specs) -> 'Sorter':
        if not self.specs:
            return self.set_specs(specs=specs)

        if specs and isinstance(specs, dict):
            if all(
                isinstance(field, str) and isinstance(reference, str)
                for field, reference in specs.items()
            ):
                self.specs.update(**specs)
        return self

    # Example: 'id' in sorter
    def __contains__(self, item) -> bool:
        if item and isinstance(item, str):
            if self.request:
                request = self.request.split(',')

                for i in request:
                    field, _ = i.split(':', maxsplit=1)

                    if item == field:
                        return True
        return False

    def as_query(self) -> Optional[str]:
        if not self.request:
            return None

        if self._query is None:
            query = []

            for i in self.request.split(','):
                if ':' not in i:
                    continue

                field, direction = i.split(':', maxsplit=1)

                if direction == 'asc' or direction == 'desc':
                    direction = direction.upper()
                else:
                    continue

                reference = self.specs.get(field)
                if reference:
                    query.append(f'{reference} {direction}')

            if query:
                self._query = 'ORDER BY {expression}'.format(expression=', '.join(query))
        return self._query

    def as_mongo_query(self) -> Optional[list]:
        if not self.request:
            return None

        if self._query is None:
            query = []

            for i in self.request.split(','):
                if ':' not in i:
                    continue

                field, direction = i.split(':', maxsplit=1)

                if direction == 'asc':
                    d = 1
                elif direction == 'desc':
                    d = -1
                else:
                    continue

                reference = self.specs.get(field)
                if reference:
                    query.append((reference, d))

            if query:
                self._mongo_query = query
        return self._mongo_query

    def as_elastic_query(self) -> Optional[list]:
        if not self.request:
            return None

        if self._elastic_query is None:
            query = [{'_score': {'order': 'desc'}}]

            for i in self.request.split(','):
                if ':' not in i:
                    continue

                field, direction = i.split(':', maxsplit=1)

                reference = self.specs.get(field)
                if reference:
                    query.append({reference: {'order': direction}})

            self._elastic_query = query
        return self._elastic_query

    def __str__(self) -> str:
        return f'{self.__class__.__name__}(request={self.request}, specs={self.specs})'

    def __repr__(self) -> str:
        return str(self)
