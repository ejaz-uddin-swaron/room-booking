from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('upload-profile-image/', views.UploadProfileImageView.as_view(), name='upload-profile-image'),
    path('tenant-profile/', views.TenantProfileView.as_view(), name='tenant-profile'),
    path('manage-role/', views.ManageUserRoleView.as_view(), name='manage-role'),
    path('users/', views.ListUsersView.as_view(), name='list-users'),
]