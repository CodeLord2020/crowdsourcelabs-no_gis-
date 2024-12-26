from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from accounts.models import UserLocation
# from django.contrib.gis.db import models as gis_models
from django.utils import timezone
from datetime import timedelta
from django.core.exceptions import ValidationError
from cddpresources.models import Resource
from incident.models import Skill
from cloud_resource.models import EventResources
from volunteer.models import Volunteer
User = get_user_model()



class EventTag(models.Model):
    """Tags for categorizing resources"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name}"


class EventCategory(models.Model):
    """Categories for classifying different types of events"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # For frontend icon representation
    
    class Meta:
        verbose_name = "Event Category"
        verbose_name_plural = "Event Categories"
        ordering = ['name']

    def __str__(self):
        return self.name
    

class EventPriority(models.TextChoices):
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'
    URGENT = 'URGENT', 'Urgent'



class EventStatus(models.TextChoices):
    DRAFT = 'DRAFT', 'Draft'
    PENDING = 'PENDING', 'Pending Approval'
    APPROVED = 'APPROVED', 'Approved'
    ACTIVE = 'ACTIVE', 'Active'
    IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
    COMPLETED = 'COMPLETED', 'Completed'
    CANCELLED = 'CANCELLED', 'Cancelled'
    POSTPONED = 'POSTPONED', 'Postponed'



class Event(models.Model):
    """
    Main event model for organizing volunteer activities and resource collection
    """
    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField()
    category = models.ForeignKey(
        EventCategory,
        on_delete=models.PROTECT,
        related_name='events'
    )
    status = models.CharField(
        max_length=20,
        choices=EventStatus.choices,
        default=EventStatus.DRAFT
    )
    priority = models.CharField(
        max_length=20,
        choices=EventPriority.choices,
        default=EventPriority.MEDIUM
    )

    # Temporal Information
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    registration_deadline = models.DateTimeField()
    
    # Spatial Information
    location_name = models.CharField(max_length=200)
    # location = gis_models.PointField()
    address = models.TextField()


    min_volunteers = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Minimum number of volunteers needed"
    )
    max_volunteers = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Maximum number of volunteers allowed"
    )
    current_volunteers = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)]
    )

    required_resources = models.ManyToManyField(
        Resource,
        through='EventResourceRequirement',
        related_name='events_required_in'
    )
    
    # Organizational Information
    organizer = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='organized_events'
    )
    coordinators = models.ManyToManyField(
        User,
        related_name='coordinated_events',
        blank=True
    )

    is_virtual = models.BooleanField(default=False)
    virtual_meeting_link = models.URLField(blank=True, null=True)
    prerequisites = models.TextField(blank=True)
    skills_required = models.ManyToManyField(Skill,blank=True, related_name='event_skills',)
    equipment_provided = models.TextField(blank=True)
    media = models.ManyToManyField(
        EventResources,
        blank=True,
        related_name='events'
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)
    tags = models.ManyToManyField(EventTag, blank=True)

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"
        ordering = ['-start_date', 'priority']
        indexes = [
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['category', 'status']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def clean(self):
        if self.end_date <= self.start_date:
            raise ValidationError({
                'end_date': 'End date must be after start date'
            })
        if self.registration_deadline >= self.start_date:
            raise ValidationError({
                'registration_deadline': 'Registration deadline must be before start date'
            })
        if self.max_volunteers < self.min_volunteers:
            raise ValidationError({
                'max_volunteers': 'Maximum volunteers must be greater than or equal to minimum volunteers'
            })

    def save(self, *args, **kwargs):
        # If this is a new event (no pk) and status is draft, send notification
        if not self.pk and self.status == EventStatus.DRAFT:
            super().save(*args, **kwargs)
            # #send mail to admins for event approval
        else:
            super().save(*args, **kwargs)

    @property
    def is_registration_open(self) -> bool:
        return (
            self.status == EventStatus.APPROVED and
            timezone.now() <= self.registration_deadline and
            self.current_volunteers < self.max_volunteers
        )

    @property
    def volunteers_needed(self) -> int:
        return max(0, self.min_volunteers - self.current_volunteers)

    @property
    def available_spots(self) -> int:
        return max(0, self.max_volunteers - self.current_volunteers)

    @property
    def is_upcoming(self) -> bool:
        return self.start_date > timezone.now()

    @property
    def is_ongoing(self) -> bool:
        now = timezone.now()
        return self.start_date <= now <= self.end_date
    
    def delete(self, *args, **kwargs):
        if self.media:
            self.media.delete()
        super().delete(*args, **kwargs)

    def get_resource_requirements(self):
        return self.eventresourcerequirement_set.all()
    



class EventResourceRequirement(models.Model):
    """Tracks resource requirements for specific events"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    quantity_required = models.IntegerField(validators=[MinValueValidator(1)])
    quantity_fulfilled = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    priority = models.CharField(
        max_length=20,
        choices=EventPriority.choices,
        default=EventPriority.MEDIUM
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Event Resource Requirement"
        verbose_name_plural = "Event Resource Requirements"
        unique_together = ['event', 'resource']
        ordering = ['priority', 'resource__name']

    def __str__(self):
        return f"{self.resource.name} for {self.event.title}"

    @property
    def quantity_needed(self) -> int:
        return max(0, self.quantity_required - self.quantity_fulfilled)

    @property
    def is_fulfilled(self) -> bool:
        return self.quantity_fulfilled >= self.quantity_required
    


class EventVolunteer(models.Model):
    """Tracks volunteer signups for events"""
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='event_volunteers'
    )
    volunteer = models.ForeignKey(
        Volunteer,
        on_delete=models.CASCADE,
        related_name='event_signups'
    )
    signup_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('APPROVED', 'Approved'),
            ('DECLINED', 'Declined'),
            ('CANCELLED', 'Cancelled'),
            ('COMPLETED', 'Completed'),
            ('NO_SHOW', 'No Show')
        ],
        default='PENDING'
    )
    assigned_role = models.CharField(max_length=100, blank=True)
    hours_logged = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    feedback = models.TextField(blank=True)
    check_in_time = models.DateTimeField(null=True, blank=True)
    check_out_time = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Event Volunteer"
        verbose_name_plural = "Event Volunteers"
        unique_together = ['event', 'volunteer']
        ordering = ['signup_date']

    def __str__(self):
        return f"{self.volunteer.user.get_full_name()} - {self.event.title}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if is_new and self.status == 'APPROVED':
            self.event.current_volunteers += 1
            self.event.save()
            # #send mail to volunteer about approval
        super().save(*args, **kwargs)

    @property
    def is_active(self) -> bool:
        return self.status == 'APPROVED'

    @property
    def can_check_in(self) -> bool:
        if self.status != 'APPROVED':
            return False
        event_start = self.event.start_date
        earliest_checkin = event_start - timedelta(hours=1)
        return earliest_checkin <= timezone.now() <= self.event.end_date