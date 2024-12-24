from rest_framework import serializers
from accounts.serializers import UserSerializer
from .models import Skill, Volunteer, VolunteerRating, VolunteerSkill
from django.utils import timezone
from django.db import transaction
# from django.contrib.gis.geos import Point
from django.db.models import Avg, Count


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'category', 'description']
        read_only_fields = ['created_at', 'updated_at']


class VolunteerSkillSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)
    skill_id = serializers.IntegerField(write_only=True)
    verified_by_name = serializers.CharField(source='verified_by.full_name', read_only=True)

    class Meta:
        model = VolunteerSkill
        fields = [
            'id', 'skill', 'skill_id', 'proficiency_level',
            'verified', 'verified_by', 'verified_by_name'
        ]
        read_only_fields = ['created_at', 'updated_at', 'verified', 'verified_by']

    def validate_proficiency_level(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError(
                "Proficiency level must be between 1 and 5"
            )
        return value


class VolunteerRatingSerializer(serializers.ModelSerializer):
    rated_by_name = serializers.CharField(source='rated_by.full_name', read_only=True)
    
    class Meta:
        model = VolunteerRating
        fields = [
            'id', 'rating', 'comments', 'created_at',
            'rated_by', 'rated_by_name'
        ]
        read_only_fields = ['created_at', 'rated_by']

    def validate(self, attrs):
        # Prevent self-rating
        if attrs['rated_by'] == attrs['volunteer'].user:
            raise serializers.ValidationError("Cannot rate yourself")
        
        # Check if user has already rated this volunteer
        if VolunteerRating.objects.filter(
            volunteer=attrs['volunteer'],
            rated_by=attrs['rated_by']
        ).exists():
            raise serializers.ValidationError("You have already rated this volunteer")
            
        return attrs


class VolunteerSerializer(serializers.ModelSerializer):
    skills = VolunteerSkillSerializer(source='volunteerskill_set', many=True, required=False)
    ratings = VolunteerRatingSerializer(source='volunteerrating_set', many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    total_ratings = serializers.IntegerField(read_only=True)
    # preferred_location = serializers.SerializerMethodField()
    latitude = serializers.FloatField(write_only=True, required=False)
    longitude = serializers.FloatField(write_only=True, required=False)

    class Meta:
        model = Volunteer
        fields = ['id', 'user', 'skills', 'availability', 'experience_level',
                 'latitude', 'longitude', 'max_travel_distance', 
                 'verified_hours', 'rating', 'is_available', 'ratings', 
                 'average_rating', 'total_ratings']
        read_only_fields = ['created_at', 'updated_at', 'verified_hours', 'rating']

    def validate(self, attrs):
        """Validate location data"""
        if 'latitude' in attrs or 'longitude' in attrs:
            if not ('latitude' in attrs and 'longitude' in attrs):
                raise serializers.ValidationError(
                    "Both latitude and longitude must be provided together"
                )
            if not (-90 <= attrs['latitude'] <= 90):
                raise serializers.ValidationError(
                    "Latitude must be between -90 and 90"
                )
            if not (-180 <= attrs['longitude'] <= 180):
                raise serializers.ValidationError(
                    "Longitude must be between -180 and 180"
                )
        return attrs

    # def get_location(self, obj):
    #     if obj.preferred_location:
    #         return {
    #             'latitude': obj.preferred_location.y,
    #             'longitude': obj.preferred_location.x
    #         }
    #     return None
    
    # def get_preferred_location(self, obj):
    #     """Convert PointField to lat/lng dict"""
    #     if obj.preferred_location:
    #         return {
    #             'latitude': obj.preferred_location.y,
    #             'longitude': obj.preferred_location.x
    #         }
    #     return None

    def validate_availability(self, value):
        required_keys = ['weekday', 'weekend', 'emergency']
        if not all(key in value for key in required_keys):
            raise serializers.ValidationError(
                "Availability must include weekday, weekend, and emergency status"
            )
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        skills_data = validated_data.pop('volunteerskill_set', [])
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)

        # if latitude is not None and longitude is not None:
        #     validated_data['preferred_location'] = Point(
        #         longitude, latitude, srid=4326
        #     )

        volunteer = Volunteer.objects.create(**validated_data)

        # Create VolunteerSkill instances from skill_ids
        for skill_data in skills_data:
            skill_id = skill_data.get('skill_id')
            try:
                skill = Skill.objects.get(id=skill_id)
                VolunteerSkill.objects.create(
                    volunteer=volunteer,
                    skill=skill,
                    proficiency_level=skill_data.get('proficiency_level'),
                    verified=False
                )
            except Skill.DoesNotExist:
                raise serializers.ValidationError(f"Skill with id {skill_id} does not exist")

        return volunteer


    @transaction.atomic
    def update(self, instance, validated_data):
        skills_data = validated_data.pop('volunteerskill_set', None)
        latitude = validated_data.pop('latitude', None)
        longitude = validated_data.pop('longitude', None)

        # if latitude is not None and longitude is not None:
        #     validated_data['preferred_location'] = Point(
        #         longitude, latitude, srid=4326
        #     )

        # Update volunteer instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update skills if provided
        if skills_data is not None:
            # Remove existing skills
            instance.volunteerskill_set.all().delete()
            
            # Add new skills
            for skill_data in skills_data:
                skill_id = skill_data.get('skill_id')
                try:
                    skill = Skill.objects.get(id=skill_id)
                    VolunteerSkill.objects.create(
                        volunteer=instance,
                        skill=skill,
                        proficiency_level=skill_data.get('proficiency_level'),
                        verified=False
                    )
                except Skill.DoesNotExist:
                    raise serializers.ValidationError(f"Skill with id {skill_id} does not exist")

        return instance