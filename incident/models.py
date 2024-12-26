from django.db import models
# from django.contrib.gis.db import models as gis_models
# from django.contrib.gis.geos import Point
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from typing import List, Dict, Any
import uuid
from django.contrib.auth import get_user_model
from cloud_resource.models import IncidentMediaResource
from cddpresources.models import Resource
from responders.models import Responder
from volunteer.models import Skill, Volunteer
from accounts.models import User
from reporters.models import Reporter




class IncidentCategory(models.Model):
    """Categories for different types of incidents/requests for help"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    severity_level = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        help_text="1: Minor, 5: Critical"
    )
    requires_verification = models.BooleanField(default=False)
    requires_immediate_response = models.BooleanField(default=False)
    requires_professional_responder = models.BooleanField(default=False)
    auto_notify_authorities = models.BooleanField(default=False)
    estimated_response_time = models.IntegerField(  # in minutes
        null=True,
        blank=True,
        help_text="Estimated time for first response"
    )
    required_skills = models.ManyToManyField(Skill, blank=True)
    parent_category = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='subcategories'
    )
    
    class Meta:
        verbose_name_plural = "incident categories"
        ordering = ['severity_level', 'name']

    def __str__(self):
        return f"{self.name} (Severity: {self.severity_level})"




class Incident(models.Model):
    """Core model for tracking incidents and help requests"""
    STATUS_CHOICES = [
        ('REPORTED', 'Reported'),
        ('VERIFIED', 'Verified'),
        ('RESPONDING', 'Responding'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
        ('INVALID', 'Invalid')
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
        ('EMERGENCY', 'Emergency')
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(IncidentCategory, on_delete=models.PROTECT)
    reporter = models.ForeignKey(Reporter, on_delete=models.PROTECT)
    # location = gis_models.PointField()
    address = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='REPORTED'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='MEDIUM'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='verified_incidents'
    )
    assigned_responders = models.ManyToManyField(
        Responder,
        through='IncidentAssignment',
        related_name='assigned_incidents'
    )
    assigned_volunteers = models.ManyToManyField(
        Volunteer,
        through='IncidentVolunteer',
        related_name='assigned_incidents'
    )
    is_sensitive = models.BooleanField(default=False)
    is_anonymous = models.BooleanField(default=False)
    estimated_resolution_time = models.IntegerField(
        null=True,
        blank=True,
        help_text="Estimated time to resolve in minutes"
    )
    estimated_people_affected = models.IntegerField(null=True, blank=True)
    media_files = models.JSONField(default=list)  # URLs to images/videos
    media_resource = models.ManyToManyField(IncidentMediaResource, related_name="incident_media")  # uploaded media resources
    tags = models.JSONField(default=list)
    required_skills = models.ManyToManyField(Skill, related_name="incident_skills")
    required_resources = models.ManyToManyField(
        Resource,
        through='IncidentResource',
        related_name='incidents_needed'
    )
    class Meta:
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['created_at']),
            models.Index(fields=['category', 'status']),
        ]

    @property
    def response_time(self) -> int:
        """Returns response time in minutes"""
        if self.status in ['REPORTED', 'VERIFIED']:
            return 0
        first_response = self.incident_timeline.filter(
            status_changed_to__in=['RESPONDING', 'IN_PROGRESS']
        ).first()
        if first_response:
            return int((first_response.created_at - self.created_at).total_seconds() / 60)
        return 0

    @property
    def is_overdue(self) -> bool:
        """Check if incident has exceeded estimated resolution time"""
        if not self.estimated_resolution_time:
            return False
        time_elapsed = (timezone.now() - self.created_at).total_seconds() / 60
        return time_elapsed > self.estimated_resolution_time

    def assign_responder(self, responder: Responder, role: str = 'PRIMARY'):
        """Assign a responder to the incident"""
        IncidentAssignment.objects.create(
            incident=self,
            responder=responder,
            role=role
        )

    def add_update(self, user: User, content: str, status_change: str = None):
        """Add an update to the incident timeline"""
        return IncidentUpdate.objects.create(
            incident=self,
            user=user,
            content=content,
            status_changed_to=status_change
        )
    
    def __str__(self):
        return f"{self.title} {self.category.name} (Priority: {self.priority})"
    


class IncidentUpdate(models.Model):
    """Track updates and changes to incidents"""
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='incident_timeline'
    )
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status_changed_to = models.CharField(
        max_length=20,
        choices=Incident.STATUS_CHOICES,
        null=True,
        blank=True
    )

    media_files = models.JSONField(default=list)  # URLs to images/videos
    media_resource = models.ManyToManyField(IncidentMediaResource, related_name="incidentupdate_media")  # uploaded media resources
    

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.incident.title} (Updated By: {self.user.full_name})"




class Task(models.Model):
    """Tasks that can be assigned to volunteers"""
    title = models.CharField(max_length=200)
    description = models.TextField()
    incident = models.ForeignKey(
        Incident,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('IN_PROGRESS', 'In Progress'),
            ('COMPLETED', 'Completed'),
            ('CANCELLED', 'Cancelled')
        ],
        default='PENDING'
    )
    priority = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        default=3
    )
    required_skills = models.ManyToManyField(Skill, blank=True)
    estimated_time = models.IntegerField(  # in minutes
        null=True,
        blank=True
    )
    due_date = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='created_tasks'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_overdue(self) -> bool:
        if not self.due_date:
            return False
        return timezone.now() > self.due_date

    def assign_volunteer(self, volunteer: 'Volunteer'):
        incident_volunteer, created = IncidentVolunteer.objects.get_or_create(
            incident=self.incident,
            volunteer=volunteer
        )
        incident_volunteer.tasks.add(self)
        # incident_volunteer.save()

    def get_volunteers(self):
        return Volunteer.objects.filter(incidentvolunteer__tasks=self)

    def __str__(self):
        return f"{self.title} (Incident: {self.incident.title})"




class IncidentAssignment(models.Model):
    """Track responder assignments to incidents"""
    ROLE_CHOICES = [
        ('PRIMARY', 'Primary Responder'),
        ('SECONDARY', 'Secondary Responder'),
        ('SUPERVISOR', 'Supervisor'),
        ('SPECIALIST', 'Specialist')
    ]

    incident = models.ForeignKey(Incident, on_delete=models.CASCADE)
    responder = models.ForeignKey(Responder, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    assigned_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['incident', 'responder']

    def __str__(self):
        return f"{self.responder} (Incident: {self.incident.title})"



class IncidentVolunteer(models.Model):
    """Track volunteer assignments to incidents"""
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE)
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    hours_contributed = models.FloatField(default=0)
    tasks = models.ManyToManyField(Task, related_name='task_volunteers')

    def __str__(self):
        return f"{self.volunteer.user.full_name} (Incident: {self.incident.title})"




class IncidentResource(models.Model):
    """Track resources allocated to incidents"""
    STATUS_CHOICES = [
        ('REQUESTED', 'Requested'),
        ('PARTIALLY_ALLOCATED', 'Partially Allocated'),
        ('FULLY_ALLOCATED', 'Fully Allocated'),
        ('RETURNED', 'Returned'),
        ('CONSUMED', 'Consumed'),
        ('CANCELLED', 'Cancelled')
    ]
    
    RETURN_STATUS_CHOICES = [
        ('PENDING', 'Return Pending'),
        ('SUBMITTED', 'Return Submitted'),
        ('VERIFIED', 'Return Verified'),
        ('REJECTED', 'Return Rejected')
    ]
    
    return_status = models.CharField(
        max_length=20,
        choices=RETURN_STATUS_CHOICES,
        null=True,
        blank=True
    )
    incident = models.ForeignKey(Incident, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    quantity_requested = models.IntegerField()
    quantity_allocated = models.IntegerField(default=0)
    requested_at = models.DateTimeField(auto_now_add=True)
    allocated_at = models.DateTimeField(null=True, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    requested_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True,
        related_name='resource_requests'
    )
    allocated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='resource_allocations'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='REQUESTED'
    )
    return_status = models.CharField(
        max_length=20,
        choices=RETURN_STATUS_CHOICES,
        null=True,
        blank=True
    )
    return_verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='verified_returns'
    )
    return_verified_at = models.DateTimeField(null=True, blank=True)
    return_notes = models.TextField(blank=True)
    partial_returns = models.JSONField(
        default=list,
        help_text="Track history of partial returns [{quantity: int, date: datetime, verified_by: int}]"
    )
    notes = models.TextField(blank=True)
    priority = models.CharField(
        max_length=20,
        choices=Incident.PRIORITY_CHOICES,
        default='MEDIUM'
    )
    expected_return_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.resource.name} (Incident: {self.incident.title})"
    
    class Meta:
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['incident', 'resource']),
            models.Index(fields=['requested_at']),
        ]

    def __str__(self):
        return f"{self.resource.name} (Incident: {self.incident.title})"

    @property
    def pending_quantity(self):
        """Returns quantity still pending allocation"""
        return self.quantity_requested - self.quantity_allocated

    @property
    def is_fully_allocated(self):
        """Check if requested quantity has been fully allocated"""
        return self.quantity_allocated >= self.quantity_requested

    @property
    def allocation_percentage(self):
        """Calculate percentage of requested resources that have been allocated"""
        if self.quantity_requested == 0:
            return 0
        return (self.quantity_allocated / self.quantity_requested) * 100
    
    def update_status(self):
        """Update status based on current allocation"""
        if self.quantity_allocated == 0:
            self.status = 'REQUESTED'
        elif self.quantity_allocated < self.quantity_requested:
            self.status = 'PARTIALLY_ALLOCATED'
        else:
            self.status = 'FULLY_ALLOCATED'
        self.save()

