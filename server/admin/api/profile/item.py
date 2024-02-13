from datetime import datetime

from core.db import db
from core.handlers import BaseAPIView
from utils.ints import IntUtils
from utils.lists import ListUtils
from utils.strs import StrUtils


class ProfileView(BaseAPIView):
    template_name = 'admin/profile.html'

    async def get(self, request, user):
        customer = await db.fetchrow(
            '''
            SELECT *
            FROM public.users
            WHERE id = $1
            ''',
            user['id']
        ) or {}

        roles = ListUtils.to_list_of_dicts(await db.fetch(
            '''
            SELECT *
            FROM public.roles
            WHERE status >= 0
            '''
        ))

        return self.success(request=request, user=user, data={
            'customer': dict(customer),
            'roles': roles,
        })

    async def put(self, request, user):

        action = StrUtils.to_str(request.json.get('action'))

        if action == 'change_info':
            first_name = StrUtils.to_str(request.json.get('first_name'))
            last_name = StrUtils.to_str(request.json.get('last_name'))
            middle_name = StrUtils.to_str(request.json.get('middle_name'))
            birthday = StrUtils.to_str(request.json.get('birthday'))
            username = StrUtils.to_str(request.json.get('username'))
            role_id = IntUtils.to_int(request.json.get('role_id'))
            photo = StrUtils.to_str(request.json.get('photo'))

            if not first_name or not last_name:
                return self.error(message='Required param(s): first_name or last_name')

            if username:
                duplicate = await db.fetchrow(
                    '''
                    SELECT *
                    FROM public.users
                    WHERE id <> $1 AND username = $2
                    ''',
                    user['id'],
                    username
                )
                if duplicate:
                    return self.error(message='Duplicate: username')

            else:
                return self.error(message='Required param(s): username')

            if not role_id:
                return self.error(message='Required param(s): role_id')

            user = await db.fetchrow(
                '''
                UPDATE public.users
                SET 
                    last_name = $2,
                    first_name = $3, 
                    middle_name = $4, 
                    role_id = $5,
                    username = $6, 
                    photo = $7,
                    birthday = $8
                WHERE id = $1
                RETURNING *
                ''',
                user['id'],
                last_name,
                first_name,
                middle_name,
                role_id,
                username,
                photo,
                datetime.strptime(birthday, '%Y-%m-%d') if birthday else None,
            )

            if not user:
                return self.error(message='Operation failed')

        return self.success()
