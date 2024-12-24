from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import (
    User, Role, UserRole, UserLocation,
)
from volunteer.models import Volunteer
from reporters.models import Reporter
from .utils import send_registration_email
from django.db import transaction
from django.contrib.auth.password_validation import validate_password
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from cloud_resource.serializers import ProfilePicResourceSerializer
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)



class UserLocationSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLocation
        fields = "__all__"


class UserLocationSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()
    last_updated = serializers.SerializerMethodField()

    class Meta:
        model = UserLocation
        fields = [
            'id', 'location_accuracy', 'location_updated_at',
            'address', 'device_info', 'user_email', 'last_updated'
        ]
        read_only_fields = ['location_updated_at']
        extra_kwargs = {
            'location_accuracy': {'required': False},
            'device_info': {'required': False},
            'address': {'required': False}
        }

    def get_user_email(self, obj):
        return obj.user.email if hasattr(obj, 'user') and obj.user else None

    def get_last_updated(self, obj):
        if obj.location_updated_at:
            return {
                'timestamp': obj.location_updated_at,
                'humanized': obj.location_updated_at.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'age_minutes': (timezone.now() - obj.location_updated_at).total_seconds() / 60
            }
        return None

    def validate(self, data):
        # Validate basic fields, no GIS-related checks
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
    location = UserLocationSerializer(required=False)
    profile_picture_data = ProfilePicResourceSerializer(required=False, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'password', 'username', 'first_name', 'last_name',
            'phone_number', 'date_of_birth', 'emergency_contact',
            'emergency_phone', 'location', 'bio', 'profile_picture', 'profile_picture_data',
            'is_active', 'is_verified', 'roles',
            'last_active', 'full_name', 'is_online'
        ]
        read_only_fields = ['is_active', 'is_verified', 'last_active', 'is_online']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

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
            if not data.get('first_name') or not data.get('last_name') or not data.get('username'):
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

        if volunteer_data:
            Volunteer.objects.create(user=user, **volunteer_data)

        reporter_role = Role.objects.get(role_type='REPORTER')
        UserRole.objects.create(user=user, role=reporter_role, is_active=True)
        Reporter.objects.create(user=user)
        send_registration_email(user.email)

        return user

    def update(self, instance, validated_data):
        volunteer_data = validated_data.pop('volunteer', None)
        location_data = validated_data.pop('location', None)
        password = validated_data.pop('password', None)

        if password:
            instance.set_password(password)

        # Update basic user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Handle location update
        if location_data:
            if instance.location:
                # Update existing location
                for attr, value in location_data.items():
                    setattr(instance.location, attr, value)
                instance.location.save()
            else:
                # Create new location
                UserLocation.objects.create(user=instance, **location_data)

        # Handle volunteer data
        if volunteer_data and hasattr(instance, 'volunteer'):
            for attr, value in volunteer_data.items():
                setattr(instance.volunteer, attr, value)
            instance.volunteer.save()

        instance.save()
        return instance


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


