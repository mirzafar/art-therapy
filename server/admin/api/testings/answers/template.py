from core.handlers import BaseAPIView


class TestingsAnswersTemplatesView(BaseAPIView):
    template_name = 'admin/answers.html'

    async def get(self, request, user, question_id):
        return self.render_template(request, user)
