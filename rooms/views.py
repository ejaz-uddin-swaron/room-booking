from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Room
from .serializers import RoomSerializer
from django.db.models import Q
from .permissions import IsAdminOrReadOnly

class RoomListAPIView(generics.ListCreateAPIView):
    serializer_class = RoomSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = Room.objects.all()

        location = self.request.query_params.get('location')
        check_in = self.request.query_params.get('check_in')  # not used yet
        check_out = self.request.query_params.get('check_out')  # not used yet
        guests = self.request.query_params.get('guests')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        room_type = self.request.query_params.get('room_type')
        amenities = self.request.query_params.getlist('amenities')

        if location:
            queryset = queryset.filter(location__icontains=location)

        if guests:
            queryset = queryset.filter(maxGuests__gte=guests)

        if min_price:
            queryset = queryset.filter(price__gte=min_price)

        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        if room_type:
            queryset = queryset.filter(type__iexact=room_type)

        if amenities:
            for amenity in amenities:
                queryset = queryset.filter(amenities__contains=[amenity])

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
    authentication_classes = [JWTAuthentication]
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
