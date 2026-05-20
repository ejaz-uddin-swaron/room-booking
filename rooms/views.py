from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Room, PropertyDocument
from .serializers import RoomSerializer, PropertyDocumentSerializer, PropertyDocumentCreateSerializer
from django.db.models import Q
from .permissions import IsAdmin
from django.utils import timezone
from django.conf import settings
from core.storage_backends import supabase_storage


class RoomListAPIView(generics.ListCreateAPIView):
    """Admin-only room listing and creation."""
    serializer_class = RoomSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        queryset = Room.objects.all()
        params = self.request.query_params
        location = params.get('location')
        guests = params.get('guests')
        min_price = params.get('min_price')
        max_price = params.get('max_price')
        room_type = params.get('room_type')
        amenities = params.getlist('amenities') if hasattr(params, 'getlist') else []

        if location:
            queryset = queryset.filter(location__icontains=location)
        if guests:
            try:
                queryset = queryset.filter(max_guests__gte=int(guests))
            except (TypeError, ValueError):
                pass
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except (TypeError, ValueError):
                pass
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except (TypeError, ValueError):
                pass
        if room_type:
            queryset = queryset.filter(type__iexact=room_type)
        if amenities:
            for amenity in amenities:
                try:
                    queryset = queryset.filter(amenities__contains=[amenity])
                except Exception:
                    pass
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        data = serializer.data
        # Attach computed presence status
        today = timezone.now().date()
        from bookings_app.models import Booking
        occupied_room_ids = set(
            Booking.objects.filter(
                status__in=['pending', 'confirmed'],
                check_in__lte=today,
                check_out__gte=today
            ).values_list('room_id', flat=True)
        )
        for item in data:
            item['presenceStatus'] = 'occupied' if item['id'] in occupied_room_ids else 'vacant'
        return Response({'success': True, 'data': data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({'success': True, 'data': serializer.data}, status=201, headers=headers)


class RoomDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Admin-only room detail, update, and delete."""
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    lookup_field = 'id'
    permission_classes = [IsAdmin]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data
        today = timezone.now().date()
        from bookings_app.models import Booking
        is_occupied = Booking.objects.filter(
            room=instance,
            status__in=['pending', 'confirmed'],
            check_in__lte=today,
            check_out__gte=today
        ).exists()
        data['presenceStatus'] = 'occupied' if is_occupied else 'vacant'
        return Response({'success': True, 'data': data})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        old_images = instance.images or []
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        new_images = serializer.validated_data.get('images', old_images)
        removed_images = set(old_images) - set(new_images)
        for url in removed_images:
            supabase_storage.delete_file_from_url(url, 'images')

        self.perform_update(serializer)
        return Response({'success': True, 'data': serializer.data})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.images:
            for url in instance.images:
                supabase_storage.delete_file_from_url(url, 'images')
        self.perform_destroy(instance)
        return Response({'success': True, 'message': 'Room deleted successfully'})


class PropertyDocumentListView(generics.ListCreateAPIView):
    """Admin-only document listing and creation."""
    serializer_class = PropertyDocumentSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        room_id = self.request.query_params.get('room_id')
        qs = PropertyDocument.objects.all()
        if room_id:
            qs = qs.filter(room_id=room_id)
        return qs

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response({'success': True, 'data': serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = PropertyDocumentCreateSerializer(data=request.data)
        if serializer.is_valid():
            room_id = serializer.validated_data.pop('roomId', None)
            room = Room.objects.filter(id=room_id).first() if room_id else None
            document = serializer.save(room=room)
            return Response({'success': True, 'data': PropertyDocumentSerializer(document).data}, status=201)
        return Response({'success': False, 'error': serializer.errors}, status=400)


class PropertyDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Admin-only document detail, update, and delete."""
    queryset = PropertyDocument.objects.all()
    serializer_class = PropertyDocumentSerializer
    permission_classes = [IsAdmin]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response({'success': True, 'data': self.get_serializer(instance).data})

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'data': serializer.data})
        return Response({'success': False, 'error': serializer.errors}, status=400)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.file_url:
            bucket = getattr(settings, 'SUPABASE_DOCUMENTS_BUCKET', 'documents')
            supabase_storage.delete_file_from_url(instance.file_url, bucket)
        instance.delete()
        return Response({'success': True, 'message': 'Document deleted'})


class PropertyDocumentUploadView(APIView):
    """Admin-only document file upload to Supabase Storage."""
    permission_classes = [IsAdmin]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'success': False, 'error': 'No file uploaded', 'status': 400}, status=400)

        bucket = getattr(settings, 'SUPABASE_DOCUMENTS_BUCKET', 'documents')

        try:
            url = supabase_storage.upload_document(file, bucket_name=bucket, folder='property-documents')
            return Response({'success': True, 'data': {'url': url}})
        except Exception as exc:
            return Response({'success': False, 'error': str(exc), 'status': 500}, status=500)
