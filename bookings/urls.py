from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from rest_framework import permissions

from drf_yasg.views import get_schema_view
from drf_yasg import openapi


def root_view(request):
    return JsonResponse({
        'status': 'ok',
        'message': 'Room Booking API is running',
        'docs': '/swagger/',
    })


schema_view = get_schema_view(
    openapi.Info(
        title="Booking Auth API",
        default_version='v1',
        description="API documentation for Booking Platform",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    url='https://room-booking-pjo6.onrender.com/' if not settings.DEBUG else None,
)


urlpatterns = [
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/rooms/', include('rooms.urls')),
    path('api/', include('core.urls')),
    path('api/bookings/', include('bookings_app.urls')),

     # Swagger paths
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
