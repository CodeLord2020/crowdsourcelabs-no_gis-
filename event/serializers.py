from rest_framework import serializers
from django.utils import timezone
from .models import (
    Event, EventCategory, EventStatus, EventTag, EventResourceRequirement, EventVolunteer
)
from accounts.models import User
from volunteer.models import Volunteer
from cddpresources.models import Resource


class EventTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventTag
        fields = '__all__'

class EventCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EventCategory
        fields = ('id', 'name', 'description', 'icon')


class EventResourceRequirementSerializer(serializers.ModelSerializer):
    resource = serializers.PrimaryKeyRelatedField(queryset=Resource.objects.all())
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())

    class Meta:
        model = EventResourceRequirement
        fields = ('id', 'event', 'resource', 'quantity_required', 'quantity_fulfilled', 'priority', 'notes')


class EventVolunteerSerializer(serializers.ModelSerializer):
    event = serializers.PrimaryKeyRelatedField(queryset=Event.objects.all())
    volunteer = serializers.PrimaryKeyRelatedField(queryset=Volunteer.objects.all())

    class Meta:
        model = EventVolunteer
        fields = ('id', 'event', 'volunteer', 'signup_date', 'status', 'assigned_role', 'hours_logged', 'feedback', 'check_in_time', 'check_out_time')


class EventSerializer(serializers.ModelSerializer):
    category = EventCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=EventCategory.objects.all(), source='category', write_only=True
    )
    organizer = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='organizer'
    )
    coordinators = serializers.PrimaryKeyRelatedField(
        many=True, queryset=User.objects.all(), required=False
    )
    location = serializers.SerializerMethodField()
    resource_requirements = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = (
            'id', 'title', 'slug', 'description', 'category', 'category_id', 'status',
            'priority', 'start_date', 'end_date', 'registration_deadline', 'location_name',
            'location', 'address', 'min_volunteers', 'max_volunteers', 'current_volunteers',
            'organizer', 'coordinators', 'is_virtual', 'virtual_meeting_link', 'prerequisites',
            'skills_required', 'equipment_provided', 'created_at', 'updated_at', 'is_featured',
            'resource_requirements'
        )

    def get_location(self, obj):
        if obj.location:
            return {
                'latitude': obj.location.y,
                'longitude': obj.location.x
            }
        return {}

    def get_resource_requirements(self, obj):
        requirements = obj.get_resource_requirements()
        return EventResourceRequirementSerializer(requirements, many=True).data

    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError(
                {'end_date': 'End date must be after start date'}
            )
        if data['registration_deadline'] >= data['start_date']:
            raise serializers.ValidationError(
                {'registration_deadline': 'Registration deadline must be before start date'}
            )
        if data['max_volunteers'] < data['min_volunteers']:
            raise serializers.ValidationError(
                {'max_volunteers': 'Maximum volunteers must be greater than or equal to minimum volunteers'}
            )
        return data