from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register('list', views.ClientViewset)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', views.UserRegistrationApiView.as_view(), name='register'),
    path('jwt/login/', views.CustomUserLoginView.as_view(), name='jwt-login'),
    path('jwt/refresh/', TokenRefreshView.as_view(), name='jwt-refresh'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('user-info/<str:username>/', views.GetUserInfoByUsername.as_view(), name='get-user-info'),
]