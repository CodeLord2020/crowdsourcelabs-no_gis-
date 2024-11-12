from django.contrib import admin
from .models import EventTag, EventResourceRequirement, EventCategory, Event, EventVolunteer
from django.contrib.gis.admin import GISModelAdmin


@admin.register(EventTag)
class ResourceTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    list_filter = ('name',)
    search_fields = ('name',)
    ordering = ('name',)



@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'icon')
    list_filter = ('name',)
    search_fields = ('name', 'description')




@admin.register(Event)
class EventAdmin(GISModelAdmin):
    list_display = (
        'title', 'category', 'status', 'priority', 'start_date',
        'end_date', 'min_volunteers', 'max_volunteers', 'current_volunteers',
        'organizer', 'is_virtual'
    )
    list_filter = (
        'category', 'status', 'priority', 'is_virtual',
        'start_date', 'end_date'
    )
    search_fields = ('title', 'description', 'location_name')
    ordering = ('-start_date',)



@admin.register(EventResourceRequirement)
class EventResourceRequirementAdmin(admin.ModelAdmin):
    list_display = (
        'event', 'resource', 'quantity_required', 'quantity_fulfilled',
        'priority'
    )
    list_filter = ('event', 'resource', 'priority')
    search_fields = ('event__title', 'resource__name')



@admin.register(EventVolunteer)
class EventVolunteerAdmin(admin.ModelAdmin):
    list_display = (
        'event', 'volunteer', 'signup_date', 'status', 'assigned_role',
        'hours_logged', 'check_in_time', 'check_out_time'
    )
    list_filter = ('event', 'status', 'assigned_role')
    search_fields = ('event__title', 'volunteer__user__username')
    ordering = ('-signup_date',)