from django.contrib import admin
from .models import ResourceTag, Resource, ResourceDonation, ResourceType



@admin.register(ResourceTag)
class ResourceTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    ordering = ('name',)



@admin.register(ResourceType)
class ResourceTypeAdmin(admin.ModelAdmin):
    """Admin configuration for resource types."""
    list_display = ('name', 'description')
    search_fields = ('name',)
    ordering = ['name']



@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    """Admin configuration for resources."""
    list_display = (
        'name', 
        'resource_type', 
        'quantity_available', 
        'quantity_allocated', 
        'unit', 
        'owner', 
        'manager', 
        'is_consumable', 
        'needs_reorder',
    )
    list_filter = ('resource_type', 'is_consumable', 'is_perishable', 'is_sharable')
    search_fields = ('name', 'description', 'owner__username', 'manager__username')
    ordering = ['name']
    list_editable = ('quantity_available', 'quantity_allocated')
    readonly_fields = ('quantity_available_for_allocation', 'needs_reorder')
    fieldsets = (
        (None, {
            'fields': ('name', 'resource_type', 'description', 'tags')
        }),
        ('Quantity Details', {
            'fields': (
                'quantity_available', 
                'quantity_allocated', 
                'minimum_quantity', 
                'reorder_point', 
                'quantity_available_for_allocation', 
                'needs_reorder'
            )
        }),
        ('Additional Details', {
            'fields': (
                'unit', 
                'cost_per_unit', 
                'expiry_date', 
                'location', 
                'is_consumable', 
                'is_perishable', 
                'is_sharable'
            )
        }),
        ('Management', {
            'fields': ('owner', 'manager')
        }),
    )
    filter_horizontal = ('tags',)
    autocomplete_fields = ['resource_type', 'owner', 'manager']
    list_per_page = 20

    def needs_reorder(self, obj):
        """Highlight reorder status with a color."""
        return '✅' if obj.needs_reorder else '❌'
    needs_reorder.short_description = 'Needs Reorder'




@admin.register(ResourceDonation)
class ResourceDonationAdmin(admin.ModelAdmin):
    """Admin configuration for resource donations."""
    list_display = (
        'resource', 
        'donor_name', 
        'quantity', 
        'monetary_value', 
        'donation_date', 
        'is_anonymous', 
        'receipt_issued'
    )
    list_filter = ('donation_date', 'is_anonymous', 'receipt_issued')
    search_fields = ('resource__name', 'donor__first_name', 'donor__last_name')
    date_hierarchy = 'donation_date'
    readonly_fields = ('donation_date',)
    fieldsets = (
        (None, {
            'fields': ('resource', 'quantity', 'monetary_value', 'is_anonymous', 'receipt_issued', 'notes')
        }),
        ('Donor Information', {
            'fields': ('donor',),
            'description': 'Specify the donor (if not anonymous)'
        }),
    )
    autocomplete_fields = ['resource', 'donor']
    list_per_page = 20

    def donor_name(self, obj):
        """Display donor name or 'Anonymous'."""
        return obj.donor.full_name if obj.donor and not obj.is_anonymous else 'Anonymous'
    donor_name.short_description = 'Donor'