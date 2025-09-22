from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Room
from .serializers import RoomSerializer
from django.db.models import Q
from .permissions import IsAdminOrReadOnly

class RoomListAPIView(generics.ListCreateAPIView):
    serializer_class = RoomSerializer
    permission_classes = [IsAdminOrReadOnly]

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
        # Map serializer data camelCase already handled by serializer
        serializer = self.get_serializer(queryset, many=True)
        return Response({'success': True, 'data': serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({'success': True, 'data': serializer.data}, status=201, headers=headers)

class RoomDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    lookup_field = 'id'
    permission_classes = [IsAdminOrReadOnly]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'success': True, 'data': serializer.data})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({'success': True, 'data': serializer.data})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'success': True, 'message': 'Room deleted successfully'})
