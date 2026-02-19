from django.urls import path
from .views import BookingsView, UpdateBookingStatusView, UserBookingsView

urlpatterns = [
    path('', BookingsView.as_view(), name='bookings'),  # GET for admin, POST to create
    path('user-bookings/', UserBookingsView.as_view(), name='user-bookings'),
    path('<int:pk>/status/', UpdateBookingStatusView.as_view(), name='update-booking-status'),
]
