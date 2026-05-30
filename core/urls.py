from django.urls import path
from .views import (
    UploadImagesView, AdminStatsView, VerifyTokenView, MeView,
    NotificationListView, NotificationMarkReadView, NotificationMarkAllReadView,
)

urlpatterns = [
    path('upload/images', UploadImagesView.as_view(), name='upload-images'),
    path('admin/stats', AdminStatsView.as_view(), name='admin-stats'),
    path('auth/verify', VerifyTokenView.as_view(), name='auth-verify'),
    path('me', MeView.as_view(), name='auth-me'),
    # Notifications
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('notifications/<int:pk>/read/', NotificationMarkReadView.as_view(), name='notification-read'),
    path('notifications/read-all/', NotificationMarkAllReadView.as_view(), name='notifications-read-all'),
]
