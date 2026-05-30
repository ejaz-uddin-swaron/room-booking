from django.contrib import admin
from .models import Booking, TenantAssignment, RentSchedule, RentPayment

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'user', 'check_in', 'check_out', 'status', 'total_price')
    list_filter = ('status', 'check_in')
    search_fields = ('room__name', 'user__username', 'user__email')

@admin.register(TenantAssignment)
class TenantAssignmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'room', 'property_name', 'start_date', 'status', 'monthly_rent')
    list_filter = ('status', 'property_name')
    search_fields = ('tenant__username', 'tenant__email', 'room__name', 'property_name')

@admin.register(RentSchedule)
class RentScheduleAdmin(admin.ModelAdmin):
    list_display = ('id', 'room_name', 'tenant_name', 'monthly_rent', 'due_day', 'status')
    list_filter = ('status', 'due_day')
    search_fields = ('room_name', 'tenant_name', 'tenant_email')

@admin.register(RentPayment)
class RentPaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'schedule', 'due_date', 'paid_date', 'amount', 'paid_amount', 'status')
    list_filter = ('status', 'due_date')
    search_fields = ('schedule__tenant_name', 'schedule__room_name')
