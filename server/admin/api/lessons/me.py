from core.handlers import BaseAPIView


class LessonsMeTemplateView(BaseAPIView):
    template_name = 'admin/lessons-me.html'

    async def get(self, request, user):
        return self.render_template(
            request=request,
            user=user
        )
