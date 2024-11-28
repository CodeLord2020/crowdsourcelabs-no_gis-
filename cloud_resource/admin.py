from django.contrib import admin
from .models import Resources, BlogResource, ProfilePicResource, IncidentMediaResource, CSRResourceMedia, EventResources





from django.contrib import admin
from django.forms import ModelForm
from django import forms
from cloudinary.uploader import upload, destroy



class ResourceForm(ModelForm):
    file = forms.FileField(required=False, help_text="Upload a file to Cloudinary")

    class Meta:
        model = ProfilePicResource
        fields = ["title", "type", "file"]  


class ResourceAdminBase(admin.ModelAdmin):
    form = ResourceForm
    list_display = ("title", "type", "size", "media_url", "created_at")
    readonly_fields = ("size", "media_url", "cloud_id", "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        # If a new file is uploaded, handle the Cloudinary logic
        file = form.cleaned_data.get("file")
        if file:
            if obj.pk and obj.cloud_id:  # If updating, delete the old Cloudinary resource
                destroy(public_id=obj.cloud_id, resource_type="raw")

            # Upload the new file to Cloudinary
            upload_result = upload(file, resource_type="raw")
            obj.media_url = upload_result["url"]
            obj.cloud_id = upload_result["public_id"]
            obj.size = upload_result["bytes"]

        super().save_model(request, obj, form, change)




@admin.register(Resources)
class ResourcesAdmin(ResourceAdminBase):
    """Admin for general resources."""

    fieldsets = (
        (None, {
            'fields': ('title', 'type', 'size', 'media_url', 'cloud_id')
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )


@admin.register(BlogResource)
class BlogResourceAdmin(ResourceAdminBase):
    """Admin for blog-related resources."""
    pass


@admin.register(EventResources)
class EventResourcesAdmin(ResourceAdminBase):
    """Admin for blog-related resources."""
    pass


@admin.register(ProfilePicResource)
class ProfilePicResourceAdmin(ResourceAdminBase):
    """Admin for profile picture resources."""
    pass



@admin.register(CSRResourceMedia)
class CSRResourceMediaAdmin(ResourceAdminBase):
    """Admin for profile picture resources."""
    pass

@admin.register(IncidentMediaResource)
class IncidentResourceAdmin(ResourceAdminBase):
    """Admin for incident-related resources."""

    list_display = ResourceAdminBase.list_display + ('is_sensitive', 'caption')
    list_filter = ResourceAdminBase.list_filter + ('is_sensitive',)
    fieldsets = (
        (None, {
            'fields': ('title', 'type', 'size', 'media_url', 'cloud_id', 'is_sensitive', 'caption')
        }),
        ('Advanced options', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )



