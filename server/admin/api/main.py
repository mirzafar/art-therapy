from core.handlers import BaseAPIView


class MainView(BaseAPIView):
    template_name = 'admin/index.html'

    async def get(self, request, user):
        return self.success(request=request, user=user)
