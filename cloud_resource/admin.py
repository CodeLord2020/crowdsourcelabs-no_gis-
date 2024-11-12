from django.contrib import admin
from .models import Resources, BlogResource, ProfilePicResource, IncidentMediaResource, CSRResourceMedia, EventResources

class ResourceAdminBase(admin.ModelAdmin):
    """Base admin configuration for resource-related models."""

    list_display = ('title', 'type', 'size', 'created_at', 'updated_at', 'cloud_id')
    search_fields = ('title', 'type', 'cloud_id')
    list_filter = ('type', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'cloud_id')

    # Custom method to format size in KB
    def formatted_size(self, obj):
        if obj.size:
            return f"{obj.size / 1024:.2f} KB"
        return "N/A"
    formatted_size.short_description = 'Size (KB)'

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



