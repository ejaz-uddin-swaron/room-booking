from rest_framework import serializers
from . import models
from django.contrib.auth.models import User

class ClientSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(many=False)
    class Meta:
        model = models.Client
        fields = '__all__' 
    
class UserDetailSerializer(serializers.ModelSerializer):
    mobile_no = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'mobile_no', 'role']

    def get_mobile_no(self, obj):
        client = getattr(obj, 'client', None)
        return getattr(client, 'mobile_no', '') if client else ''

    def get_role(self, obj):
        client = getattr(obj, 'client', None)
        return getattr(client, 'role', 'customer') if client else 'customer'

class ProfileUpdateSerializer(serializers.ModelSerializer):
    mobile_no = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'mobile_no']

    def update(self, instance, validated_data):
        mobile_no = validated_data.pop('mobile_no', None)

        # Update User fields
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.save()

        # Update Client fields
        if mobile_no is not None:
            client, _ = models.Client.objects.get_or_create(
                user=instance,
                defaults={'mobile_no': '', 'role': 'customer', 'image': ''}
            )
            client.mobile_no = mobile_no
            client.save()

        return instance

