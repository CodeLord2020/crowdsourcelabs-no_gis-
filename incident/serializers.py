from rest_framework import serializers
from .models import (
    Task, IncidentAssignment, IncidentVolunteer, IncidentUpdate,
    IncidentResource, Incident, IncidentCategory
)
from django.utils import timezone
from django.db import transaction
# from django.contrib.gis.geos import Point
from datetime import timedelta
from cddp.tasks import send_notification_email
from accounts.models import User
from cddp.email_templates import EmailTemplates
from drf_spectacular.utils import extend_schema_field, OpenApiTypes

class TaskSerializer(serializers.ModelSerializer):
    assigned_volunteers = serializers.SerializerMethodField()
    incident_details = serializers.SerializerMethodField()
    required_skills_details = serializers.SerializerMethodField()
    completion_status = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')

    @extend_schema_field(OpenApiTypes.STR)
    def get_status_display(self, obj):
        return f"{EmailTemplates.get_emoji_status(obj.status)} {obj.get_status_display()}"


    @extend_schema_field(list[OpenApiTypes.OBJECT])
    def get_assigned_volunteers(self, obj):
        return [{
            'id': assignment.volunteer.id,
            'name': assignment.volunteer.user.full_name,
            'experience_level': assignment.volunteer.experience_level,
            'skills': [skill.name for skill in assignment.volunteer.skills.all()]
        } for assignment in obj.volunteers.through.objects.filter(task=obj)]
     

    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_incident_details(self, obj):
        return {
            'id': obj.incident.id,
            'title': obj.incident.title,
            'status': obj.incident.status,
            'priority': obj.incident.priority
        }
    

    @extend_schema_field(list[OpenApiTypes.OBJECT])
    def get_required_skills_details(self, obj):
        return [{
            'id': skill.id,
            'name': skill.name,
            'description': skill.description
        } for skill in obj.required_skills.all()]
    


    @extend_schema_field(OpenApiTypes.OBJECT)
    def get_completion_status(self, obj):
        # Retrieve all `IncidentVolunteer` entries related to the current task
        incident_volunteers = obj.volunteers.through.objects.filter(tasks=obj)
        total_volunteers = incident_volunteers.count()

        if total_volunteers == 0:
            return {'percentage': 0, 'status': 'Not Started'}

        # Count how many of these volunteers have completed the task
        completed_count = incident_volunteers.filter(completed_at__isnull=False).count()

        # Calculate completion percentage
        percentage = (completed_count / total_volunteers) * 100
        return {
            'percentage': percentage,
            'status': obj.status,
            'completed_count': completed_count,
            'total_volunteers': total_volunteers
        }
    
    def validate(self, data):
        if data.get('due_date'):
            if data['due_date'] < timezone.now():
                raise serializers.ValidationError(
                    "Due date cannot be in the past"
                )
            if data['incident'].estimated_resolution_time:
                incident_resolution = (
                    data['incident'].created_at + 
                    timedelta(minutes=data['incident'].estimated_resolution_time)
                )
                if data['due_date'] > incident_resolution:
                    raise serializers.ValidationError(
                        "Task due date cannot be after incident's estimated resolution time"
                    )

        if data.get('required_skills'):
            incident_skills = set(data['incident'].required_skills.all())
            task_skills = set(data['required_skills'])
            if not task_skills.issubset(incident_skills):
                raise serializers.ValidationError(
                    "Task cannot require skills not required by the incident"
                )
            
        return data
    


class IncidentAssignmentSerializer(serializers.ModelSerializer):
    responder_details = serializers.SerializerMethodField()
    incident_details = serializers.SerializerMethodField()
    performance_metrics = serializers.SerializerMethodField()

    class Meta:
        model = IncidentAssignment
        fields = '__all__'
        read_only_fields = ('assigned_at', 'accepted_at', 'completed_at')


    def get_responder_details(self, obj):
        return {
            'id': obj.responder.id,
            'name': obj.responder.user.full_name,
            'organization': obj.responder.organization,
            'specializations': [s.name for s in obj.responder.specializations.all()],
            'is_certified': obj.responder.is_certified,
            'is_on_duty': obj.responder.is_on_duty
        }

    def get_incident_details(self, obj):
        return {
            'id': obj.incident.id,
            'title': obj.incident.title,
            'status': obj.incident.status,
            'priority': obj.incident.priority,
            'location': {
                'latitude': obj.incident.location.y,
                'longitude': obj.incident.location.x
            }
        }

    def get_performance_metrics(self, obj):
        if not obj.completed_at:
            return None

        response_time = (obj.accepted_at - obj.assigned_at).total_seconds() / 60
        completion_time = (obj.completed_at - obj.accepted_at).total_seconds() / 60

        return {
            'response_time_minutes': round(response_time, 2),
            'completion_time_minutes': round(completion_time, 2),
            'within_estimated_time': completion_time <= obj.incident.estimated_resolution_time
            if obj.incident.estimated_resolution_time else None
        }




class IncidentCategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    required_skills_details = serializers.SerializerMethodField()

    class Meta:
        model = IncidentCategory
        fields = '__all__'
        extra_kwargs = {
            'created_at': {'read_only': True},
            'updated_at': {'read_only': True}
        }

    def get_subcategories(self, obj):
        if obj.subcategories.exists():
            return IncidentCategorySerializer(obj.subcategories.all(), many=True).data
        return []

    def get_required_skills_details(self, obj):
        return [{
            'id': skill.id,
            'name': skill.name,
            'description': skill.description
        } for skill in obj.required_skills.all()]

    def validate(self, data):
        if data.get('parent_category'):
            if data['parent_category'] == self.instance:
                raise serializers.ValidationError(
                    "Category cannot be its own parent"
                )
            # Check for circular reference
            parent = data['parent_category']
            while parent:
                if parent == self.instance:
                    raise serializers.ValidationError(
                        "Circular reference detected in category hierarchy"
                    )
                parent = parent.parent_category
        return data



# class IncidentLocationSerializer(serializers.Serializer):
#     latitude = serializers.FloatField(min_value=-90, max_value=90)
#     longitude = serializers.FloatField(min_value=-180, max_value=180)

#     def to_internal_value(self, data):
#         data = super().to_internal_value(data)
#         return Point(data['longitude'], data['latitude'])
    



class IncidentSerializer(serializers.ModelSerializer):
    # location = IncidentLocationSerializer()
    category_details = serializers.SerializerMethodField()
    assigned_responders_count = serializers.SerializerMethodField()
    assigned_volunteers_count = serializers.SerializerMethodField()
    response_time = serializers.IntegerField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    media_resources = serializers.SerializerMethodField()

    class Meta:
        model = Incident
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'verified_at', 
                          'verified_by', 'response_time', 'is_overdue')
        
    def get_category_details(self, obj):
        return {
            'id': obj.category.id,
            'name': obj.category.name,
            'severity_level': obj.category.severity_level,
            'requires_verification': obj.category.requires_verification
        }

    def get_assigned_responders_count(self, obj):
        return obj.assigned_responders.count()

    def get_assigned_volunteers_count(self, obj):
        return obj.assigned_volunteers.count()

    def get_media_resources(self, obj):
        return [{
            'id': resource.id,
            'url': resource.media_url,
            'caption': resource.caption,
            'type': resource.type,
            'is_sensitive': resource.is_sensitive
        } for resource in obj.media_resource.all()]

    @transaction.atomic
    def create(self, validated_data):
        location_data = validated_data.pop('location')
        required_skills = validated_data.pop('required_skills', [])
        required_resources = validated_data.pop('required_resources', [])
        
        incident = Incident.objects.create(
            location=location_data,
            **validated_data
        )

        if required_skills:
            incident.required_skills.set(required_skills)
        
        if required_resources:
            for resource in required_resources:
                IncidentResource.objects.create(
                    incident=incident,
                    resource=resource['resource'],
                    quantity_requested=resource['quantity']
                )

        if incident.category.requires_verification:
            send_notification_email.delay(
                subject="🔔 New Incident Requires Verification",
                template_name='incident_verification_required',
                context={'incident': incident},
                recipient_list=[admin.email for admin in User.objects.filter(is_staff=True)]
            )

        if incident.category.auto_notify_authorities:
            send_notification_email.delay(
                subject="🚨 New Emergency Incident Reported",
                template_name='incident_authority_notification',
                context={'incident': incident},
                recipient_list=[authority.email for authority in incident.category.authorities.all()] #!!!!!! needs update
            )

        return incident

    def validate(self, data):
        # Validate priority against category severity
        if data.get('category'):
            severity_level = data['category'].severity_level
            priority_mapping = {
                1: 'LOW',
                2: 'LOW',
                3: 'MEDIUM',
                4: 'HIGH',
                5: 'CRITICAL'
            }
            if data.get('priority', 'MEDIUM') != priority_mapping[severity_level]:
                data['priority'] = priority_mapping[severity_level]

        # Validate professional responder requirement
        if data.get('category') and data['category'].requires_professional_responder:
            data['is_sensitive'] = True

        return data




class IncidentUpdateSerializer(serializers.ModelSerializer):
    user_details = serializers.SerializerMethodField()
    media_resources = serializers.SerializerMethodField()

    class Meta:
        model = IncidentUpdate
        fields = '__all__'
        read_only_fields = ('created_at',)

    def get_user_details(self, obj):
        return {
            'id': obj.user.id,
            'name': obj.user.full_name,
            'role': obj.user.get_roles()
        }

    def get_media_resources(self, obj):
        return [{
            'id': resource.id,
            'url': resource.media_url,
            'caption': resource.caption,
            'type': resource.type,
            'is_sensitive': resource.is_sensitive
        } for resource in obj.media_resource.all()]
    
    @transaction.atomic
    def create(self, validated_data):
        incident = validated_data['incident']
        previous_status = incident.status
        
        update = super().create(validated_data)
        
        if update.status_changed_to:
            incident.status = update.status_changed_to
            incident.save()
            
            # Send notifications based on status change
            if update.status_changed_to == 'VERIFIED':
                #send mail to reporter
                pass
            elif update.status_changed_to == 'RESOLVED':
                #send mail to all stakeholders
                pass
            
            # Log status change in incident timeline
            if previous_status != update.status_changed_to:
                #send mail about status change
                pass
                
        return update


    def validate(self, data):
        # Validate status transitions
        if data.get('status_changed_to'):
            current_status = data['incident'].status
            valid_transitions = {
                'REPORTED': ['VERIFIED', 'INVALID'],
                'VERIFIED': ['RESPONDING', 'INVALID'],
                'RESPONDING': ['IN_PROGRESS'],
                'IN_PROGRESS': ['RESOLVED'],
                'RESOLVED': ['CLOSED', 'IN_PROGRESS'],
                'CLOSED': [],
                'INVALID': []
            }
            
            if data['status_changed_to'] not in valid_transitions[current_status]:
                raise serializers.ValidationError(
                    f"Invalid status transition from {current_status} to {data['status_changed_to']}"
                )
        return data



class IncidentResourceSerializer(serializers.ModelSerializer):
    pending_quantity = serializers.IntegerField(read_only=True)
    allocation_percentage = serializers.FloatField(read_only=True)
    is_fully_allocated = serializers.BooleanField(read_only=True)
    resource_name = serializers.CharField(source='resource.name', read_only=True)
    incident_title = serializers.CharField(source='incident.title', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)
    allocated_by_name = serializers.CharField(source='allocated_by.get_full_name', read_only=True)
    return_verified_by_name = serializers.CharField(source='return_verified_by.get_full_name', read_only=True)

    class Meta:
        model = IncidentResource
        fields = [
            'id', 'incident', 'resource', 'resource_name', 'incident_title',
            'quantity_requested', 'quantity_allocated', 'pending_quantity', 'return_verified_by_name',
            'allocation_percentage', 'is_fully_allocated', 'status', 'notes',
            'requested_at', 'allocated_at', 'returned_at', 'priority', 'return_status',
            'requested_by', 'requested_by_name', 'allocated_by', 'return_verified_by',
            'allocated_by_name', 'expected_return_date','return_verified_at','partial_returns',
        ]
        read_only_fields = [
            'requested_at', 'allocated_at', 'returned_at',
            'requested_by', 'allocated_by'
        ]