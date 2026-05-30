from django.urls import path
from .views import (
    BookingsView, UpdateBookingStatusView,
    RentScheduleView, RentScheduleDetailView, RentPaymentView, RentReminderView,
    TenantAssignmentListView, TenantAssignmentDetailView, MyAssignmentView,
    MyRentSchedulesView, MyRentRemindersView,
)

urlpatterns = [
    path('', BookingsView.as_view(), name='bookings'),  # GET: admin list all bookings
    path('<int:pk>/status/', UpdateBookingStatusView.as_view(), name='update-booking-status'),
    path('rent-schedules/', RentScheduleView.as_view(), name='rent-schedules'),
    path('rent-schedules/<int:pk>/', RentScheduleDetailView.as_view(), name='rent-schedule-detail'),
    path('rent-schedules/<int:schedule_id>/payments/', RentPaymentView.as_view(), name='rent-payments'),
    path('rent-reminders/', RentReminderView.as_view(), name='rent-reminders'),
    # Tenant assignments (admin)
    path('tenant-assignments/', TenantAssignmentListView.as_view(), name='tenant-assignments'),
    path('tenant-assignments/<int:pk>/', TenantAssignmentDetailView.as_view(), name='tenant-assignment-detail'),
    # Tenant self-service
    path('my-assignment/', MyAssignmentView.as_view(), name='my-assignment'),
    path('my-rent-schedules/', MyRentSchedulesView.as_view(), name='my-rent-schedules'),
    path('my-rent-reminders/', MyRentRemindersView.as_view(), name='my-rent-reminders'),
]
