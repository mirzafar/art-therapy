from core.handlers import BaseAPIView


class TestingsResponsesTemplateView(BaseAPIView):
    template_name = 'admin/responses.html'

    async def get(self, request, user, result_id):
        return self.render_template(request, user)
