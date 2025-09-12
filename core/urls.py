from django.urls import path
from .views import UploadImagesView, AdminStatsView, VerifyTokenView

urlpatterns = [
    path('upload/images', UploadImagesView.as_view(), name='upload-images'),
    path('admin/stats', AdminStatsView.as_view(), name='admin-stats'),
    path('auth/verify', VerifyTokenView.as_view(), name='auth-verify'),
]
