from django.contrib import admin
from .models import (
    IncidentCategory, Incident, IncidentUpdate, Task,
    IncidentAssignment, IncidentVolunteer, IncidentResource
)





@admin.register(IncidentCategory)
class IncidentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'severity_level', 'requires_verification', 'requires_immediate_response')
    search_fields = ('name', 'description')
    list_filter = ('severity_level', 'requires_verification', 'requires_immediate_response')
    ordering = ('severity_level', 'name')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'severity_level', 'parent_category')
        }),
        ('Verification & Response', {
            'fields': (
                'requires_verification', 'requires_immediate_response',
                'requires_professional_responder', 'auto_notify_authorities'
            )
        }),
        ('Estimated Timelines', {
            'fields': ('estimated_response_time',)
        }),
        ('Required Skills', {
            'fields': ('required_skills',)
        }),
    )


from django.contrib import admin
from .models import Incident, IncidentAssignment, IncidentVolunteer, Responder, Volunteer

# Inline admin for managing responders assigned to incidents
class IncidentAssignmentInline(admin.TabularInline):
    model = IncidentAssignment
    extra = 1  # Set this to control the number of empty rows shown for adding new assignments
    autocomplete_fields = ['responder']  

# Inline admin for managing volunteers assigned to incidents
class IncidentVolunteerInline(admin.TabularInline):
    model = IncidentVolunteer
    extra = 1
    autocomplete_fields = ['volunteer'] 


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'priority', 'created_at', 'is_overdue')
    search_fields = ('title', 'description', 'address')
    list_filter = ('status', 'priority', 'category')
    ordering = ('-created_at',)
    readonly_fields = ('response_time', 'is_overdue')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'category', 'reporter', 'status', 'priority')
        }),
        ('Location & Address', {
            'fields': ('location', 'address')
        }),
        ('Verification', {
            'fields': ('verified_at', 'verified_by')
        }),
        # Removed 'assigned_responders' and 'assigned_volunteers' from fieldsets
        ('Estimated Data', {
            'fields': ('estimated_resolution_time', 'estimated_people_affected')
        }),
        ('Media & Tags', {
            'fields': ('media_files', 'media_resource', 'tags')
        }),
    )
    inlines = [IncidentAssignmentInline, IncidentVolunteerInline]



@admin.register(IncidentUpdate)
class IncidentUpdateAdmin(admin.ModelAdmin):
    list_display = ('incident', 'user', 'created_at', 'status_changed_to')
    search_fields = ('incident__title', 'user__username', 'content')
    list_filter = ('status_changed_to',)
    ordering = ('-created_at',)
    fieldsets = (
        (None, {
            'fields': ('incident', 'user', 'content')
        }),
        ('Status Change', {
            'fields': ('status_changed_to',)
        }),
        ('Media', {
            'fields': ('media_files', 'media_resource')
        }),
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'incident', 'status', 'priority', 'created_by', 'is_overdue')
    search_fields = ('title', 'description', 'incident__title')
    list_filter = ('status', 'priority')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'incident', 'status', 'priority')
        }),
        ('Estimates & Deadlines', {
            'fields': ('estimated_time', 'due_date', 'is_overdue')
        }),
        ('Assignment', {
            'fields': ('created_by',)
        }),
        ('Required Skills', {
            'fields': ('required_skills',)
        }),
    )


@admin.register(IncidentAssignment)
class IncidentAssignmentAdmin(admin.ModelAdmin):
    list_display = ('incident', 'responder', 'role', 'assigned_at', 'completed_at')
    search_fields = ('incident__title', 'responder__name')
    list_filter = ('role',)
    ordering = ('-assigned_at',)
    fieldsets = (
        (None, {
            'fields': ('incident', 'responder', 'role')
        }),
        ('Timestamps', {
            'fields': ('assigned_at', 'accepted_at', 'completed_at')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )


@admin.register(IncidentVolunteer)
class IncidentVolunteerAdmin(admin.ModelAdmin):
    list_display = ('incident', 'volunteer', 'assigned_at', 'completed_at', 'hours_contributed')
    search_fields = ('incident__title', 'volunteer__user__username')
    ordering = ('-assigned_at',)
    fieldsets = (
        (None, {
            'fields': ('incident', 'volunteer')
        }),
        ('Assignments', {
            'fields': ('tasks',)
        }),
        ('Timestamps & Hours', {
            'fields': ('assigned_at', 'accepted_at', 'completed_at', 'hours_contributed')
        }),
    )


@admin.register(IncidentResource)
class IncidentResourceAdmin(admin.ModelAdmin):
    list_display = ('incident', 'resource', 'quantity_requested', 'quantity_allocated', 'status')
    search_fields = ('incident__title', 'resource__name')
    list_filter = ('status',)
    ordering = ('-requested_at',)
    fieldsets = (
        (None, {
            'fields': ('incident', 'resource', 'quantity_requested', 'quantity_allocated')
        }),
        ('Timestamps', {
            'fields': ('requested_at', 'allocated_at', 'returned_at')
        }),
        ('Status & Notes', {
            'fields': ('status', 'notes')
        }),
    )
