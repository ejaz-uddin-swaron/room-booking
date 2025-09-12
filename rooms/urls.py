from django.urls import path
from .views import RoomListAPIView, RoomDetailAPIView

urlpatterns = [
    path('', RoomListAPIView.as_view(), name='room-list'),
    path('<str:id>', RoomDetailAPIView.as_view(), name='room-detail'),
]
