from django.urls import path
from .views import BookingsView, UpdateBookingStatusView

urlpatterns = [
    path('bookings', BookingsView.as_view(), name='bookings'),  # GET for admin, POST to create
    path('bookings/<str:booking_id>/status', UpdateBookingStatusView.as_view(), name='update-booking-status'),
]
