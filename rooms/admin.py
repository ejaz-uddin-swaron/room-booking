from django.contrib import admin
from .models import Room, PropertyDocument, PropertyImage, BookingInterest

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'price', 'location', 'available')
    list_filter = ('type', 'available', 'location')
    search_fields = ('name', 'description', 'location')

@admin.register(PropertyDocument)
class PropertyDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'property_id', 'status', 'upload_date')
    list_filter = ('type', 'status', 'property_id')
    search_fields = ('name', 'description', 'property_id', 'tenant__username')

@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'property_name', 'is_primary', 'sort_order', 'created_at')
    list_filter = ('property_name', 'is_primary')
    search_fields = ('property_name', 'caption')

@admin.register(BookingInterest)
class BookingInterestAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'phone', 'property_name', 'status', 'created_at')
    list_filter = ('status', 'property_name')
    search_fields = ('name', 'email', 'phone', 'message', 'property_name')
