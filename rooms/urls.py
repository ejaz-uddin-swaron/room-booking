from django.urls import path
from .views import (
    RoomListAPIView, RoomDetailAPIView,
    PropertyDocumentListView, PropertyDocumentDetailView, PropertyDocumentUploadView,
    PropertyImageListView, PropertyImageDetailView,
    PublicRoomListView, PublicRoomDetailView, PublicPropertyListView, PublicPropertyImagesView,
    BookingInterestView,
)

urlpatterns = [
    # Admin room CRUD
    path('', RoomListAPIView.as_view(), name='room-list'),
    path('<int:id>/', RoomDetailAPIView.as_view(), name='room-detail'),
    
    # Unified/Consolidated Property Documents (Property-level, room-linked, tenant-linked)
    path('documents/', PropertyDocumentListView.as_view(), name='property-documents-list'),
    path('documents/<int:pk>/', PropertyDocumentDetailView.as_view(), name='property-documents-detail'),
    path('documents/upload/', PropertyDocumentUploadView.as_view(), name='property-documents-upload'),
    
    # Backward compatibility aliases pointing to the consolidated views
    path('property-documents/', PropertyDocumentListView.as_view(), name='property-document-list-compat'),
    path('property-documents/<int:pk>/', PropertyDocumentDetailView.as_view(), name='property-document-detail-compat'),
    path('property-documents/upload/', PropertyDocumentUploadView.as_view(), name='property-document-upload-compat'),
    path('tenant-documents/', PropertyDocumentListView.as_view(), name='tenant-document-list-compat'),
    path('tenant-documents/<int:pk>/', PropertyDocumentDetailView.as_view(), name='tenant-document-detail-compat'),
    path('tenant-documents/upload/', PropertyDocumentUploadView.as_view(), name='tenant-document-upload-compat'),
    path('tenant-documents/<int:pk>/review/', PropertyDocumentDetailView.as_view(), name='tenant-document-review-compat'),

    # Admin property-level images
    path('property-images/', PropertyImageListView.as_view(), name='property-image-list'),
    path('property-images/<int:pk>/', PropertyImageDetailView.as_view(), name='property-image-detail'),
    
    # Public endpoints (no auth)
    path('public/', PublicRoomListView.as_view(), name='public-room-list'),
    path('public/<int:id>/', PublicRoomDetailView.as_view(), name='public-room-detail'),
    path('public/properties/', PublicPropertyListView.as_view(), name='public-property-list'),
    path('public/properties/<str:property_name>/images/', PublicPropertyImagesView.as_view(), name='public-property-images'),
    path('public/interest/', BookingInterestView.as_view(), name='booking-interest'),
]

