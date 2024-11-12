from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from .models import Volunteer, Skill, VolunteerSkill


@admin.register(Volunteer)
class VolunteerAdmin(GISModelAdmin):  # Using GIS admin for map support on preferred_location
    list_display = ('user', 'experience_level', 'verified_hours', 'rating', 'is_available')
    list_filter = ('experience_level', 'is_available')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('rating', 'verified_hours')
    
    fieldsets = (
        (None, {
            'fields': ('user', 'experience_level', 'verified_hours', 'rating', 'is_available')
        }),
        ('Location', {
            'fields': ('preferred_location', 'max_travel_distance')
        }),
        ('Availability', {
            'fields': ('availability',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:  # Only update rating if this is an edit, not a new instance
            obj.update_rating()
        super().save_model(request, obj, form, change)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category')
    list_filter = ('category',)
    search_fields = ('name', 'category')
    ordering = ('category', 'name')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'category', 'description')
        }),
    )


class VolunteerSkillInline(admin.TabularInline):
    model = VolunteerSkill
    extra = 1
    readonly_fields = ('verified', 'verified_by')
    can_delete = True


@admin.register(VolunteerSkill)
class VolunteerSkillAdmin(admin.ModelAdmin):
    list_display = ('volunteer', 'skill', 'proficiency_level', 'verified', 'verified_by')
    list_filter = ('verified', 'proficiency_level')
    search_fields = ('volunteer__user__email', 'skill__name')
    
    fieldsets = (
        (None, {
            'fields': ('volunteer', 'skill', 'proficiency_level', 'verified', 'verified_by')
        }),
    )
    autocomplete_fields = ['volunteer', 'skill']


# Linking Skill inlines to Volunteer for better manageability
VolunteerAdmin.inlines = [VolunteerSkillInline]
