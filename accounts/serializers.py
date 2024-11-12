from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.gis.geos import Point
from .models import (
    User, Role, UserRole, UserLocation,
)
from volunteer.models import Volunteer
from reporters.models import Reporter
from .utils import send_registration_email
from django.db import transaction
from .services import LocationService
from django.contrib.auth.password_validation import validate_password
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from datetime import timedelta
from django.utils import timezone
from cloud_resource.serializers import ProfilePicResourceSerializer



class LocationSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)
    coordinates = serializers.SerializerMethodField()
    
    class Meta:
        model = UserLocation
        fields = ['id', 'user', 'coordinates', 'latitude', 'longitude', 'location_accuracy', 
                 'location_updated_at', 'address', 'device_info']
        read_only_fields = ['location_updated_at']#, 'address']

    def get_coordinates(self, obj):
        if obj.coordinates:
            return {'latitude': obj.coordinates[0], 'longitude': obj.coordinates[1]}
        return None
    
    def validate(self, data):
        lat = data.pop('latitude', None)
        lon = data.pop('longitude', None)

        if lat is not None and lon is not None:
            try:
                data['location'] = Point(float(lon), float(lat), srid=4326)
                # Try to get address if not provided
                if not data.get('address'):
                    address = LocationService.get_address_from_coordinates(lat, lon)
                    if address:
                        data['address'] = address
            except (ValueError, TypeError) as e:
                raise serializers.ValidationError(f"Invalid coordinates: {e}")
        
        return data
    


class UserRoleSerializer(serializers.ModelSerializer):
    role_type = serializers.CharField(source='role.role_type', read_only=True)
    
    class Meta:
        model = UserRole
        fields = ['id', 'role_type', 'role', 'assigned_by', 'assigned_at', 'is_active']
        read_only_fields = ['assigned_at', 'assigned_by']

    def validate(self, data):
        if data.get('role').role_type == 'SUPERADMIN':
            user = self.context['request'].user
            if not user.has_role('SUPERADMIN'):
                raise serializers.ValidationError(
                    "Only superadmins can assign superadmin roles"
                )
        return data
    



class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    roles = UserRoleSerializer(source='userrole_set', many=True, read_only=True)
    current_location = serializers.SerializerMethodField()
    # profile_picture = ProfilePicResourceSerializer(required =False)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'password', 'first_name', 'last_name',
            'phone_number', 'date_of_birth', 'emergency_contact',
            'emergency_phone', 'current_location', 'bio', 'profile_picture', 'is_active',
            'is_verified', 'roles', 'volunteer',
            'last_active', 'full_name', 'is_online'
        ]
        read_only_fields = ['is_active', 'is_verified', 'last_active', 'is_online']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def get_current_location(self, obj):

        latest_location = obj.user_locations.order_by('-location_updated_at').first()
        if latest_location:
            return {
                'latitude': latest_location.coordinates[0],  
                'longitude': latest_location.coordinates[1],
                'accuracy': latest_location.location_accuracy,  
                'updated_at': latest_location.location_updated_at
            }
        elif not latest_location:
            request = self.context.get('request')
            print("tried to get by IP")
            if request:
                ip_address = request.META.get('REMOTE_ADDR')
                coords = LocationService.get_coordinates_from_ip(ip_address)
                if coords:
                    print(f"got the cord {coords}")
                    loc = UserLocation.objects.create(
                        user=request.user,
                        location=Point(coords['longitude'], coords['latitude']),
                        location_accuracy=coords['accuracy'],
                        device_info={'source': 'ip_geolocation', 'ip': ip_address}
                    )
                    return {
                        'latitude': coords['latitude'],  
                        'longitude': coords['longitude'],
                        'accuracy': ['accuracy'], 
                    }           
        else:
            return None

    def validate_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(str(e))
        return value

    def validate(self, data):
        if 'volunteer' in data and not data.get('phone_number'):
            raise serializers.ValidationError(
                "Phone number is required for volunteers"
            )
        
        if self.instance is None:  # Creation only
            if not data.get('first_name') or not data.get('last_name'):
                raise serializers.ValidationError(
                    "First name and last name are required"
                )
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        location_data = validated_data.pop('location', None)
        password = validated_data.pop('password')
        volunteer_data = validated_data.pop('volunteer', None)

       # Create user
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()


        if location_data:
            UserLocation.objects.create(user=user, **location_data)
        else:
            # Try to get location from IP
            request = self.context.get('request')
            if request:
                ip_address = request.META.get('REMOTE_ADDR')
                coords = LocationService.get_coordinates_from_ip(ip_address)
                if coords:
                    UserLocation.objects.create(
                        user=user,
                        location=Point(coords['longitude'], coords['latitude']),
                        location_accuracy=coords['accuracy'],
                        device_info={'source': 'ip_geolocation', 'ip': ip_address}
                    )

        if volunteer_data:
            Volunteer.objects.create(user=user, **volunteer_data)

        reporter_role = Role.objects.get(role_type='REPORTER')

        UserRole.objects.create(
            user=user,
            role=reporter_role,
            is_active=True
        )
        Reporter.objects.create(user=user)
        send_registration_email(user.email)

        return user

    def update(self, instance, validated_data):
        volunteer_data = validated_data.pop('volunteer', None)
        location_data = validated_data.pop('location', None)
        password = validated_data.pop('password', None)

        if password:
            instance.set_password(password)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if volunteer_data and hasattr(instance, 'volunteer'):
            for attr, value in volunteer_data.items():
                setattr(instance.volunteer, attr, value)
            instance.volunteer.save()
        
        if location_data:
            location, _ = UserLocation.objects.get_or_create(user=instance)
            location_serializer = LocationSerializer(
                location,
                data=location_data,
                partial=True
            )
            if location_serializer.is_valid():
                location_serializer.save()

        instance.save()
        return instance
    


    # def create(self, validated_data):
    #     lat = validated_data.pop('latitude')
    #     lon = validated_data.pop('longitude')
    #     location = Point(lon, lat, srid=4326)
    #     validated_data['location'] = location
        
    #     # Try to get address using LocationService
    #     address = LocationService.get_address_from_coordinates(lat, lon)
    #     if address:
    #         validated_data['address'] = address
            
    #     return super().create(validated_data)


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id', 'role_type', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("New password and confirm password do not match.")
        return data



class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

 

class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "Password fields didn't match."})
        return data

    def save(self):
        uid = self.validated_data['uid']
        token = self.validated_data['token']
        new_password = self.validated_data['new_password']
        
        try:
            uid = urlsafe_base64_decode(uid).decode()
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"uid": "Invalid value"})
        
        if not default_token_generator.check_token(user, token):
            raise serializers.ValidationError({"token": "Invalid value"})

        user.set_password(new_password)
        user.save()
        return user


