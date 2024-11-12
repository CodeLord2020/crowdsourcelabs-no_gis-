from django.contrib import admin
from django.utils import timezone
from .models import Responder, Specialization


@admin.register(Responder)
class ResponderAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'certification_number', 'certification_expiry', 'is_on_duty', 'is_certified')
    list_filter = ('is_on_duty', 'specializations')
    search_fields = ('user__email', 'organization', 'certification_number')
    readonly_fields = ('is_certified', 'last_deployment')

    fieldsets = (
        (None, {
            'fields': ('user', 'organization', 'certification_number', 'certification_expiry', 'is_on_duty', 'last_deployment')
        }),
        ('Specializations', {
            'fields': ('specializations',)
        }),
    )

    def is_certified(self, obj):
        """Shows if the responder’s certification is currently valid."""
        return obj.is_certified
    is_certified.boolean = True  # Displays a tick or cross icon


@admin.register(Specialization)
class SpecializationAdmin(admin.ModelAdmin):
    list_display = ('name', 'required_certification')
    search_fields = ('name',)
    list_filter = ('required_certification',)


