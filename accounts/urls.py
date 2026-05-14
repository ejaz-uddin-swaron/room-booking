from django.urls import path
from . import views

urlpatterns = [
    path('user-info/<str:username>/', views.GetUserInfoByUsername.as_view(), name='get-user-info'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('upload-profile-image/', views.UploadProfileImageView.as_view(), name='upload-profile-image'),
]