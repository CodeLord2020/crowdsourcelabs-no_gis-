from django.db import models
from django.contrib.auth.models import  AbstractUser
from django.core.validators import RegexValidator, MinLengthValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .managers import UserManager
from typing import List
import uuid
from django.core.exceptions import ValidationError
from django.contrib.gis.db import models
from .mixins import LocationMixin
from cloud_resource.models import ProfilePicResource
from django.utils.crypto import get_random_string
# Create your models here.




class User(AbstractUser):
    """Base user model with enhanced fields and functionality"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None  # Remove username field
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
    profile_picture = models.ForeignKey(ProfilePicResource, null=True, blank=True, on_delete=models.SET_NULL)
    last_active = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    # location = models.PointField(null=True, blank=True)
    # location = models.OneToOneField(UserLocation, null=True, blank=True,  on_delete=models.SET_NULL)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
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
        if self.last_active:
            return (timezone.now() - self.last_active).seconds < 300
        return False

    def get_roles(self) -> List[str]:
        return [role.role_type for role in self.user_roles.all()]

    def has_role(self, role_type: str) -> bool:
        return self.user_roles.filter(role__role_type=role_type).exists()

    
    def delete(self, *args, **kwargs):
        if self.profile_picture:
            self.profile_picture.delete()
        super().delete(*args, **kwargs)


class UserLocation(LocationMixin):
    """Model to track user location history"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name= 'user_locations')
    device_info = models.JSONField(
        default=dict,
        help_text="Information about the device that reported location"
    )

    class Meta:
        indexes = [
            models.Index(fields=['location_updated_at']),
        ]
        ordering = ['-location_updated_at']

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



