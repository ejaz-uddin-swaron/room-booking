from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

router = DefaultRouter()
router.register('list', views.ClientViewset)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', views.UserRegistrationApiView.as_view(), name='register'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('user-info/<str:username>/', views.GetUserInfoByUsername.as_view(), name='get-user-info'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('upload-profile-image/', views.UploadProfileImageView.as_view(), name='upload-profile-image'),
]