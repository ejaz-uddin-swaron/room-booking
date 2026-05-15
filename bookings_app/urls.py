from django.urls import path
from .views import (
    BookingsView, UpdateBookingStatusView,
    RentScheduleView, RentScheduleDetailView, RentPaymentView, RentReminderView
)

urlpatterns = [
    path('', BookingsView.as_view(), name='bookings'),  # GET: admin list all bookings
    path('<int:pk>/status/', UpdateBookingStatusView.as_view(), name='update-booking-status'),
    path('rent-schedules/', RentScheduleView.as_view(), name='rent-schedules'),
    path('rent-schedules/<int:pk>/', RentScheduleDetailView.as_view(), name='rent-schedule-detail'),
    path('rent-schedules/<int:schedule_id>/payments/', RentPaymentView.as_view(), name='rent-payments'),
    path('rent-reminders/', RentReminderView.as_view(), name='rent-reminders'),
]
