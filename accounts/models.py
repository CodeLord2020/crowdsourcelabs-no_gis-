from django.db import models
from django.contrib.auth.models import  AbstractUser
from django.core.validators import RegexValidator, MinLengthValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .managers import UserManager
from typing import List
import uuid
from django.contrib.gis.db import models as gismodel
from django.contrib.gis.geos import Point
from django.core.validators import MinValueValidator, MaxValueValidator
import logging
from django.core.exceptions import ValidationError
from django.contrib.gis.db import models
from .mixins import LocationMixin
from cloud_resource.models import ProfilePicResource
from django.utils.crypto import get_random_string
# Create your models here.
logger = logging.getLogger(__name__)





class UserLocation(gismodel.Model):
    """Model to store user's current location"""
    location = models.PointField(
        srid=4326,  # Using WGS84 coordinate system (standard for GPS)
        null=True,
        blank=True,
        help_text="Geographic location (longitude, latitude)"
    )
    location_accuracy = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Accuracy of location in meters"
    )
    location_updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Last time location was updated"
    )
    address = models.TextField(
        blank=True,
        help_text="Human-readable address"
    )
    device_info = models.JSONField(
        default=dict,
        help_text="Information about the device that reported location"
    )

    class Meta:
        indexes = [
            models.Index(fields=['location_updated_at']),
        ]
        ordering = ['-location_updated_at']

    def __str__(self):
        coords = self.coordinates
        if coords:
            return f"Location at {coords[0]:.6f}, {coords[1]:.6f}"
        return "Location not set"

    def update_location(self, latitude, longitude, accuracy=None):
        """Update location with new coordinates"""
        try:
            self.location = Point(float(longitude), float(latitude), srid=4326)
            if accuracy is not None:
                self.location_accuracy = accuracy
            self.save()
            logger.info(f"Location updated for user {self.user} to: {self.coordinates} with accuracy {accuracy}")
            return True
        except (ValueError, TypeError) as e:
            logger.error(f"Location update failed for user {self.user}: {e}")
            return False

    @property
    def coordinates(self):
        """Return tuple of (latitude, longitude)"""
        if self.location:
            return (self.location.y, self.location.x)
        return None




class User(AbstractUser):
    """Base user model with enhanced fields and functionality"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(_('email address'), unique=True)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'"
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True
    )
    date_of_birth = models.DateField(null=True, blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True
    )
    bio = models.TextField(blank=True)
    profile_picture = models.OneToOneField(ProfilePicResource, null=True, blank=True, on_delete=models.SET_NULL)
    last_active = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    location = models.OneToOneField(
        UserLocation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='user'
    )
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', username]
    
    objects = UserManager()
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            models.Index(fields=['email', 'is_active']),
        ]

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_online(self) -> bool:
        if self.last_login:
            return (timezone.now() - self.last_login).seconds < 300
        return False

    def get_roles(self) -> List[str]:
        # return [role.role_type for role in self.user_roles.all()]
        return list(
            self.user_roles.filter(is_active=True)
            .select_related('role')
            .values_list('role__role_type', flat=True)
        )

    def has_role(self, role_type: str) -> bool:
        return self.user_roles.filter(role__role_type=role_type).exists()

    
    def delete(self, *args, **kwargs):
        if self.profile_picture:
            self.profile_picture.delete()
        super().delete(*args, **kwargs)







# class UserLocation(LocationMixin):
#     """Model to track user location history"""
#     user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name= 'user_locations')
#     device_info = models.JSONField(
#         default=dict,
#         help_text="Information about the device that reported location"
#     )

#     class Meta:
#         indexes = [
#             models.Index(fields=['location_updated_at']),
#         ]
#         ordering = ['-location_updated_at']

    # def latest_location(self):
    #     return self.user.locations.order_by('-location_updated_at').first()


class Role(models.Model):
    """Base role model defining different user roles"""
    ROLE_CHOICES = [
        ('VOLUNTEER', 'Volunteer'),
        ('RESPONDER', 'Responder'),
        ('REPORTER', 'Reporter'),
        ('ADMIN', 'Admin'),
        ('SUPERADMIN', 'Super Admin'),
    ]
    
    role_type = models.CharField(max_length=20, choices=ROLE_CHOICES, unique=True)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('role')
        verbose_name_plural = _('roles')

    def __str__(self):
        return self.role_type
    

class UserRole(models.Model):
    """Intermediary model for user-role relationship"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_roles')  # First FK
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='role_assignments',
        verbose_name='Assigned By'  # Optional: for clarity in admin
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('user', 'role')
        indexes = [
            models.Index(fields=['user', 'role', 'is_active']),
        ]

    def clean(self):
        if self.role.role_type == 'SUPERADMIN' and not self.assigned_by.has_role('SUPERADMIN') and not self.user.is_superuser:
            raise ValidationError("Only superadmins can assign superadmin roles")



