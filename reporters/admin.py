from django.contrib import admin
from django.utils import timezone
from .models import  Reporter



@admin.register(Reporter)
class ReporterAdmin(admin.ModelAdmin):
    list_display = ('user', 'credibility_score', 'reports_submitted', 'reports_verified', 'verification_rate')
    readonly_fields = ('credibility_score', 'verification_rate')

    fieldsets = (
        (None, {
            'fields': ('user', 'credibility_score', 'reports_submitted', 'reports_verified')
        }),
    )

    def save_model(self, request, obj, form, change):
        """Updates the credibility score when a Reporter instance is saved."""
        if change:  # Only update credibility if editing an existing instance
            obj.update_credibility_score()
        super().save_model(request, obj, form, change)

    def verification_rate(self, obj):
        """Shows the reporter’s verification rate as a percentage."""
        return f"{obj.verification_rate * 100:.1f}%"


