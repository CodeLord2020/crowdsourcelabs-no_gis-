from django.db import models
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from typing import List, Dict, Any
import uuid
from accounts.models import User
from cloud_resource.models import CSRResourceMedia


class ResourceTag(models.Model):
    """Tags for categorizing resources"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name}"


class ResourceType(models.Model):
    """Defines types of resources"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Resource Type"
        verbose_name_plural = "Resource Types"
        ordering = ['name']

    def __str__(self):
        return self.name
    

    
class Resource(models.Model):
    """Track available resources and supplies"""
    name = models.CharField(max_length=100)
    resource_type = models.ForeignKey(ResourceType,on_delete=models.PROTECT,related_name='resources')
    description = models.TextField()
    minimum_quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    reorder_point = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(0)])
    quantity_available = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    quantity_allocated = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    media = models.ManyToManyField(CSRResourceMedia, blank= True, related_name="resources_media")
    unit = models.CharField(max_length=50)
    expiry_date = models.DateField(null=True, blank=True)
    location = gis_models.PointField(null=True, blank=True)
    owner = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='owned_resources'
    )
    manager = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='managed_resources'
    )
    is_consumable = models.BooleanField(default=True)
    is_perishable = models.BooleanField(default=False)
    is_sharable = models.BooleanField(default=True)
    cost_per_unit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    tags = models.ManyToManyField(ResourceTag, blank=True)

    class Meta:
        verbose_name = "Resource"
        verbose_name_plural = "Resources"
        ordering = ['name']

    @property
    def quantity_available_for_allocation(self) -> int:
        return max(0, self.quantity_available - self.quantity_allocated)

    @property
    def needs_reorder(self) -> bool:
        return self.reorder_point is not None and self.quantity_available <= self.reorder_point
    
    def delete(self, *args, **kwargs):
        if self.media:
            self.media.delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (Resource Type: {self.resource_type})"





class ResourceDonation(models.Model):
    """Track donations of resources"""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    donor = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='donations'
    )
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    donation_date = models.DateTimeField(auto_now_add=True)
    monetary_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_anonymous = models.BooleanField(default=False)
    receipt_issued = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Resource Donation"
        verbose_name_plural = "Resource Donations"
        ordering = ['-donation_date']

    def __str__(self):
        donor_name = self.donor.full_name if self.donor and not self.is_anonymous else 'Anonymous'
        return f"{self.resource.name} (Donated By: {donor_name})"