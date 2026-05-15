from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('upload-profile-image/', views.UploadProfileImageView.as_view(), name='upload-profile-image'),
]