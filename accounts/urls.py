from rest_framework.routers import DefaultRouter
from django.urls import path, include
from . import views
from rest_framework.authtoken.views import obtain_auth_token

router = DefaultRouter()
router.register('list', views.ClientViewset)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', views.UserRegistrationApiView.as_view(), name='register'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('user-info/<str:username>/', views.GetUserInfoByUsername.as_view(), name='get-user-info'),
    path('login/', obtain_auth_token, name='login'),
]