from core.handlers import BaseAPIView


class LessonsTemplateView(BaseAPIView):
    template_name = 'admin/lessons.html'

    async def get(self, request, user):
        return self.render_template(
            request=request,
            user=user
        )
