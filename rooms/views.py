from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import Room, PropertyDocument, PropertyImage, BookingInterest
from .serializers import (
    RoomSerializer, PublicRoomSerializer,
    PropertyDocumentSerializer,
    PropertyImageSerializer,
    BookingInterestSerializer, BookingInterestCreateSerializer,
)
from django.db.models import Q
from .permissions import IsAdmin, IsTenant, IsAdminOrTenant
from django.utils import timezone
from django.conf import settings
from core.storage_backends import supabase_storage


# ─── Admin Room Views (existing) ──────────────────────────────────────────────


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


# ─── Public Room/Property Views ───────────────────────────────────────────────


class PublicRoomListView(generics.ListAPIView):
    """Public: browse available rooms. No auth required."""
    serializer_class = PublicRoomSerializer
    permission_classes = []
    authentication_classes = []

    def get_queryset(self):
        queryset = Room.objects.filter(available=True)
        params = self.request.query_params
        location = params.get('location')
        room_type = params.get('room_type')
        min_price = params.get('min_price')
        max_price = params.get('max_price')
        guests = params.get('guests')

        if location:
            queryset = queryset.filter(location__icontains=location)
        if room_type:
            queryset = queryset.filter(type__iexact=room_type)
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
        if guests:
            try:
                queryset = queryset.filter(max_guests__gte=int(guests))
            except (TypeError, ValueError):
                pass
        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data})


class PublicRoomDetailView(generics.RetrieveAPIView):
    """Public: view a single available room. No auth required."""
    serializer_class = PublicRoomSerializer
    permission_classes = []
    authentication_classes = []
    queryset = Room.objects.filter(available=True)
    lookup_field = 'id'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'success': True, 'data': serializer.data})


class PublicPropertyListView(APIView):
    """Public: list properties grouped by location with images. No auth required."""
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        # Get all unique property locations that have available rooms
        rooms = Room.objects.filter(available=True).values('location').distinct()
        properties = []

        for loc_entry in rooms:
            location = loc_entry['location']
            loc_rooms = Room.objects.filter(location=location, available=True)
            images = PropertyImage.objects.filter(property_name=location)

            # Get primary image or first image
            primary_image = images.filter(is_primary=True).first()
            image_url = primary_image.image_url if primary_image else (
                images.first().image_url if images.exists() else None
            )
            # Also collect first room image as fallback
            if not image_url and loc_rooms.exists():
                first_room = loc_rooms.first()
                if first_room.images:
                    image_url = first_room.images[0] if isinstance(first_room.images, list) else None

            # Collect all unique amenities across rooms
            all_amenities = set()
            for r in loc_rooms:
                if isinstance(r.amenities, list):
                    all_amenities.update(r.amenities)

            properties.append({
                'name': location,
                'roomCount': loc_rooms.count(),
                'minPrice': float(loc_rooms.order_by('price').first().price) if loc_rooms.exists() else 0,
                'maxPrice': float(loc_rooms.order_by('-price').first().price) if loc_rooms.exists() else 0,
                'imageUrl': image_url,
                'allImages': [img.image_url for img in images[:6]],
                'amenities': sorted(list(all_amenities))[:10],
                'roomTypes': sorted(list(set(loc_rooms.values_list('type', flat=True)))),
            })

        return Response({'success': True, 'data': properties})


class PublicPropertyImagesView(APIView):
    """Public: get images for a specific property. No auth required."""
    permission_classes = []
    authentication_classes = []

    def get(self, request, property_name):
        images = PropertyImage.objects.filter(property_name=property_name)
        serializer = PropertyImageSerializer(images, many=True)
        return Response({'success': True, 'data': serializer.data})


class BookingInterestView(APIView):
    """Public: submit booking/contact interest. No auth required."""
    permission_classes = []
    authentication_classes = []

    def post(self, request):
        serializer = BookingInterestCreateSerializer(data=request.data)
        if serializer.is_valid():
            interest = serializer.save()

            # Send notification to admins
            try:
                from core.models import Notification
                from django.contrib.auth.models import User
                from accounts.models import Client
                admin_users = User.objects.filter(client__role='admin')
                for admin_user in admin_users:
                    Notification.objects.create(
                        user=admin_user,
                        title='New Booking Interest',
                        message=f'{interest.name} ({interest.email}) is interested in {interest.property_name or "a property"}.',
                        type='general',
                        link='/admin/management',
                    )
            except Exception:
                pass  # Don't fail if notification creation fails

            return Response({
                'success': True,
                'data': BookingInterestSerializer(interest).data,
                'message': 'Your interest has been submitted. Our team will contact you soon.'
            }, status=201)
        return Response({'success': False, 'error': serializer.errors}, status=400)


# ─── Admin Document Views (existing, preserved) ──────────────────────────────


# ─── Consolidated Document Views ──────────────────────────────────────────────


class PropertyDocumentListView(generics.ListCreateAPIView):
    """Consolidated document listing and creation for Admins and Tenants."""
    serializer_class = PropertyDocumentSerializer
    permission_classes = [IsAdminOrTenant]

    def get_queryset(self):
        user = self.request.user
        client = getattr(user, 'client', None)
        role = getattr(client, 'role', 'customer') if client else 'customer'

        if role == 'admin' or user.is_staff:
            # Admin can list all documents with optional filters
            qs = PropertyDocument.objects.all()
            
            property_id = self.request.query_params.get('property_id')
            room_id = self.request.query_params.get('room_id')
            tenant_id = self.request.query_params.get('tenant_id')
            assignment_id = self.request.query_params.get('assignment_id')
            status_param = self.request.query_params.get('status')
            
            is_property_level = self.request.query_params.get('is_property_level') == 'true'
            is_room_level = self.request.query_params.get('is_room_level') == 'true'
            is_tenant_level = self.request.query_params.get('is_tenant_level') == 'true'

            if property_id:
                qs = qs.filter(property_id=property_id)
            if room_id:
                qs = qs.filter(room_id=room_id)
            if tenant_id:
                qs = qs.filter(tenant_id=tenant_id)
            if assignment_id:
                qs = qs.filter(assignment_id=assignment_id)
            if status_param:
                qs = qs.filter(status=status_param)

            if is_property_level:
                qs = qs.filter(room__isnull=True, tenant__isnull=True)
            elif is_room_level:
                qs = qs.filter(room__isnull=False)
            elif is_tenant_level:
                qs = qs.filter(tenant__isnull=False)

            return qs
        else:
            # Tenants can only list their own documents or documents uploaded by them
            return PropertyDocument.objects.filter(Q(tenant=user) | Q(uploaded_by=user))

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data})

    def create(self, request, *args, **kwargs):
        user = request.user
        client = getattr(user, 'client', None)
        role = getattr(client, 'role', 'customer') if client else 'customer'

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            if role == 'tenant' and not user.is_staff:
                # Tenants can only create documents for themselves
                # Look up their active assignment to populate property, room, and assignment FKs
                from bookings_app.models import TenantAssignment
                assignment = TenantAssignment.objects.filter(tenant=user, status='active').first()
                
                room = assignment.room if assignment else None
                prop_id = room.location if room else ""
                
                doc = serializer.save(
                    tenant=user,
                    uploaded_by=user,
                    room=room,
                    property_id=prop_id,
                    assignment=assignment,
                    status='pending'  # Force pending status for tenant uploads
                )

                # Send notification to admins
                try:
                    from core.models import Notification
                    from django.contrib.auth.models import User
                    admin_users = User.objects.filter(client__role='admin')
                    for admin_user in admin_users:
                        Notification.objects.create(
                            user=admin_user,
                            title='New Document Uploaded',
                            message=f'Tenant {user.username} uploaded a new document: "{doc.name}".',
                            type='general',
                            link='/admin/management',
                        )
                except Exception:
                    pass
            else:
                # Admins can create any document
                room_id = serializer.validated_data.get('room_id') or request.data.get('roomId')
                tenant_id = serializer.validated_data.get('tenant_id') or request.data.get('tenantId')
                assignment_id = serializer.validated_data.get('assignment_id') or request.data.get('assignmentId')
                
                room = Room.objects.filter(id=room_id).first() if room_id else None
                
                # If property_id is not passed but a room exists, default to the room's location
                prop_id = serializer.validated_data.get('property_id') or request.data.get('propertyId')
                if not prop_id and room:
                    prop_id = room.location

                doc = serializer.save(
                    room=room,
                    property_id=prop_id or "",
                    tenant_id=tenant_id,
                    assignment_id=assignment_id,
                    uploaded_by=user
                )

            return Response({'success': True, 'data': self.get_serializer(doc).data}, status=201)
        return Response({'success': False, 'error': serializer.errors}, status=400)


class PropertyDocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Consolidated document detail, update, review, and delete."""
    queryset = PropertyDocument.objects.all()
    serializer_class = PropertyDocumentSerializer
    permission_classes = [IsAdminOrTenant]

    def get_object(self):
        instance = super().get_object()
        user = self.request.user
        client = getattr(user, 'client', None)
        role = getattr(client, 'role', 'customer') if client else 'customer'

        # Tenants can only access their own documents
        if role != 'admin' and not user.is_staff:
            if instance.tenant != user and instance.uploaded_by != user:
                raise PermissionDenied("You do not have permission to access this document.")
        
        return instance

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response({'success': True, 'data': self.get_serializer(instance).data})

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        client = getattr(user, 'client', None)
        role = getattr(client, 'role', 'customer') if client else 'customer'

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        if serializer.is_valid():
            old_status = instance.status

            if role != 'admin' and not user.is_staff:
                # Tenants can only update basic fields
                # Ensure they don't modify status or admin notes
                serializer.validated_data.pop('status', None)
                serializer.validated_data.pop('admin_notes', None)
                serializer.validated_data.pop('tenant_id', None)
                serializer.validated_data.pop('assignment_id', None)
                serializer.validated_data.pop('room_id', None)
                serializer.save()
            else:
                # Admins can update all fields
                serializer.save()

                # Trigger review notification if status changes (e.g. approved/rejected)
                new_status = serializer.validated_data.get('status') or request.data.get('status')
                if new_status and new_status != old_status and instance.tenant:
                    instance.reviewed_at = timezone.now()
                    instance.save(update_fields=['reviewed_at'])

                    try:
                        from core.models import Notification
                        status_text = 'approved' if new_status == 'approved' else 'rejected'
                        Notification.objects.create(
                           user=instance.tenant,
                           title=f'Document {status_text.title()}',
                           message=f'Your document "{instance.name}" has been {status_text}.' + (
                               f' Notes: {instance.admin_notes}' if instance.admin_notes else ''
                           ),
                           type='document_review',
                           link='/tenant/documents',
                        )
                    except Exception:
                        pass

            return Response({'success': True, 'data': self.get_serializer(instance).data})
        return Response({'success': False, 'error': serializer.errors}, status=400)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.file_url:
            bucket = getattr(settings, 'SUPABASE_DOCUMENTS_BUCKET', 'documents')
            supabase_storage.delete_file_from_url(instance.file_url, bucket)
        instance.delete()
        return Response({'success': True, 'message': 'Document deleted'})


class PropertyDocumentUploadView(APIView):
    """Consolidated document file upload to Supabase Storage."""
    permission_classes = [IsAdminOrTenant]

    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'success': False, 'error': 'No file uploaded'}, status=400)

        bucket = getattr(settings, 'SUPABASE_DOCUMENTS_BUCKET', 'documents')

        try:
            url = supabase_storage.upload_document(file, bucket_name=bucket, folder='documents')
            return Response({'success': True, 'data': {'url': url}})
        except Exception as exc:
            return Response({'success': False, 'error': str(exc)}, status=500)



class PropertyImageListView(generics.ListCreateAPIView):
    """Admin-only property-level image listing and creation."""
    serializer_class = PropertyImageSerializer
    permission_classes = [IsAdmin]

    def get_queryset(self):
        property_name = self.request.query_params.get('property_name')
        qs = PropertyImage.objects.all()
        if property_name:
            qs = qs.filter(property_name=property_name)
        return qs

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response({'success': True, 'data': serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': True, 'data': serializer.data}, status=201)


class PropertyImageDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Admin-only property image detail, update, and delete."""
    queryset = PropertyImage.objects.all()
    serializer_class = PropertyImageSerializer
    permission_classes = [IsAdmin]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response({'success': True, 'data': self.get_serializer(instance).data})

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': True, 'data': serializer.data})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.image_url:
            supabase_storage.delete_file_from_url(instance.image_url, 'images')
        instance.delete()
        return Response({'success': True, 'message': 'Property image deleted'})


# Note: Deprecated views for PropertyLevelDocument and TenantDocument have been consolidated into PropertyDocument views above.
