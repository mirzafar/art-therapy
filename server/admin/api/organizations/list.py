from core.db import db
from core.handlers import BaseAPIView
from utils.lists import ListUtils


class OrganizationsView(BaseAPIView):
    template_name = 'admin/organizations.html'

    async def get(self, request, user):
        request_type = request.args.get('request_type', 'html')

        organizations = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT id, title
            FROM public.organization
            WHERE status >= 0
            ORDER BY id DESC
            '''
        ))

        return self.success(request, user, data={
            'organizations': organizations
        })
