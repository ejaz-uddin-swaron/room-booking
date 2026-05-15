from django.urls import path
from .views import RoomListAPIView, RoomDetailAPIView, PropertyDocumentListView, PropertyDocumentDetailView, PropertyDocumentUploadView

urlpatterns = [
    path('', RoomListAPIView.as_view(), name='room-list'),
    path('<int:id>/', RoomDetailAPIView.as_view(), name='room-detail'),
    path('documents/', PropertyDocumentListView.as_view(), name='room-documents'),
    path('documents/<int:pk>/', PropertyDocumentDetailView.as_view(), name='room-document-detail'),
    path('documents/upload/', PropertyDocumentUploadView.as_view(), name='room-document-upload'),
]
