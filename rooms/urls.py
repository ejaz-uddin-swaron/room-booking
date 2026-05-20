from django.urls import path
from .views import (
    RoomListAPIView, RoomDetailAPIView,
    PropertyDocumentListView, PropertyDocumentDetailView, PropertyDocumentUploadView,
    PropertyImageListView, PropertyImageDetailView,
    PropertyLevelDocumentListView, PropertyLevelDocumentDetailView, PropertyLevelDocumentUploadView,
)

urlpatterns = [
    path('', RoomListAPIView.as_view(), name='room-list'),
    path('<int:id>/', RoomDetailAPIView.as_view(), name='room-detail'),
    path('documents/', PropertyDocumentListView.as_view(), name='room-documents'),
    path('documents/<int:pk>/', PropertyDocumentDetailView.as_view(), name='room-document-detail'),
    path('documents/upload/', PropertyDocumentUploadView.as_view(), name='room-document-upload'),
    # Property-level images
    path('property-images/', PropertyImageListView.as_view(), name='property-image-list'),
    path('property-images/<int:pk>/', PropertyImageDetailView.as_view(), name='property-image-detail'),
    # Property-level documents
    path('property-documents/', PropertyLevelDocumentListView.as_view(), name='property-document-list'),
    path('property-documents/<int:pk>/', PropertyLevelDocumentDetailView.as_view(), name='property-document-detail'),
    path('property-documents/upload/', PropertyLevelDocumentUploadView.as_view(), name='property-document-upload'),
]
