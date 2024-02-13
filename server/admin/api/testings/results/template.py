from core.handlers import BaseAPIView


class TestingsResultsTemplateView(BaseAPIView):
    template_name = 'admin/results.html'

    async def get(self, request, user, lesson_id):
        return self.render_template(request, user)
