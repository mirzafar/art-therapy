from core.handlers import BaseAPIView


class TestingsCompleteTemplatesView(BaseAPIView):
    template_name = 'admin/complete.html'

    async def get(self, request, user, lesson_id):
        return self.render_template(request, user)
