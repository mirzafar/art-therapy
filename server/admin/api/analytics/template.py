from core.handlers import BaseAPIView


class AnalyticsTemplateView(BaseAPIView):
    template_name = 'admin/power-bi.html'

    async def get(self, request, user):
        return self.render_template(request=request, user=user)
