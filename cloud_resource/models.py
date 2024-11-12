from django.db import models

# Create your models here.

from cloudinary.models import CloudinaryField


RESOURCE_TYPES = (
    ("AUDIO", "AUDIO"),
    ("VIDEO", "VIDEO"),
    ("IMAGE", "IMAGE"),
    ("DOCUMENT", "DOCUMENT"),
    ("OTHERS", "OTHERS"),
)


class Resources(models.Model):
    title = models.CharField(max_length=50, null=True)
    size = models.IntegerField(null=True)
    type = models.CharField(max_length=20, choices=RESOURCE_TYPES, default="IMAGE")
    media_url = models.CharField(max_length=255, blank=True, null=True)
    cloud_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self) -> str:
        return self.title
    
    class Meta:
        ordering = ["-created_at"]


class EventResources(models.Model):
    title = models.CharField(max_length=50, null=True)
    size = models.IntegerField(null=True)
    type = models.CharField(max_length=20, choices=RESOURCE_TYPES, default="IMAGE")
    media_url = models.CharField(max_length=255, blank=True, null=True)
    cloud_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self) -> str:
        return self.title
    
    class Meta:
        ordering = ["-created_at"]


class BlogResource(models.Model):
    title = models.CharField(max_length=50, null=True)
    size = models.IntegerField(null=True)
    type = models.CharField(max_length=20, choices=RESOURCE_TYPES, default="IMAGE")
    media_url = models.CharField(max_length=255, blank=True, null=True)
    cloud_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self) -> str:
        return self.title
    
    class Meta:
        ordering = ["-created_at"]



class CSRResourceMedia(models.Model):
    title = models.CharField(max_length=50, null=True)
    size = models.IntegerField(null=True)
    type = models.CharField(max_length=20, choices=RESOURCE_TYPES, default="IMAGE")
    media_url = models.CharField(max_length=255, blank=True, null=True)
    cloud_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self) -> str:
        return self.title
    
    class Meta:
        ordering = ["-created_at"]




class ProfilePicResource(models.Model):
    title = models.CharField(max_length=50, null=True)
    size = models.IntegerField(null=True)
    type = models.CharField(max_length=20, choices=RESOURCE_TYPES, default="IMAGE")
    media_url = models.CharField(max_length=255, blank=True, null=True)
    cloud_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self) -> str:
        return self.title
    
    class Meta:
        ordering = ["-created_at"]



class IncidentMediaResource(models.Model):
    title = models.CharField(max_length=50, null=True)
    size = models.IntegerField(null=True)
    type = models.CharField(max_length=20, choices=RESOURCE_TYPES, default="IMAGE")
    is_sensitive = models.BooleanField(default=False)
    caption = models.CharField(max_length=255, blank=True)
    media_url = models.CharField(max_length=255, blank=True, null=True)
    cloud_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self) -> str:
        return self.title
    
    class Meta:
        ordering = ["-created_at"]