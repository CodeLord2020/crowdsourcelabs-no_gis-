import django_filters
from django.db.models import Q, F, ExpressionWrapper, FloatField
# from django.contrib.gis.measure import D
# from django.contrib.gis.db.models.functions import Distance
from .models import (
    Task, IncidentAssignment, IncidentVolunteer, 
    IncidentResource, Incident, IncidentCategory
)
from django.utils import timezone
from accounts.models import User


class TaskFilter(django_filters.FilterSet):
    due_date_from = django_filters.DateTimeFilter(
        field_name='due_date',
        lookup_expr='gte'
    )
    due_date_to = django_filters.DateTimeFilter(
        field_name='due_date',
        lookup_expr='lte'
    )
    priority_min = django_filters.NumberFilter(
        field_name='priority',
        lookup_expr='gte'
    )
    priority_max = django_filters.NumberFilter(
        field_name='priority',
        lookup_expr='lte'
    )
    required_skills = django_filters.ModelMultipleChoiceFilter(
        field_name='required_skills',
        to_field_name='id',
        conjoined=True  # AND instead of OR
    )
    estimated_time_max = django_filters.NumberFilter(
        field_name='estimated_time',
        lookup_expr='lte'
    )
    incident_status = django_filters.ChoiceFilter(
        field_name='incident__status',
        choices=Incident.STATUS_CHOICES
    )
    overdue = django_filters.BooleanFilter(method='filter_overdue')

    class Meta:
        model = Task
        fields = {
            'status': ['exact', 'in'],
            'incident': ['exact'],
            'created_by': ['exact'],
            'priority': ['exact', 'in'],
        }

    def filter_overdue(self, queryset, name, value):
        return queryset.filter(due_date__lt=timezone.now()) if value else queryset




class IncidentAssignmentFilter(django_filters.FilterSet):
    assigned_after = django_filters.DateTimeFilter(
        field_name='assigned_at',
        lookup_expr='gte'
    )
    assigned_before = django_filters.DateTimeFilter(
        field_name='assigned_at',
        lookup_expr='lte'
    )
    completion_time = django_filters.NumberFilter(
        method='filter_completion_time'
    )
    incident_priority = django_filters.ChoiceFilter(
        field_name='incident__priority',
        choices=Incident.PRIORITY_CHOICES
    )
    responder_specialization = django_filters.ModelMultipleChoiceFilter(
        field_name='responder__specializations',
        to_field_name='id',
        conjoined=True
    )

    class Meta:
        model = IncidentAssignment
        fields = {
            'role': ['exact', 'in'],
            'incident': ['exact'],
            'responder': ['exact'],
            'accepted_at': ['isnull'],
            'completed_at': ['isnull'],
        }

    def filter_completion_time(self, queryset, name, value):
        return queryset.annotate(
            completion_time=ExpressionWrapper(
                F('completed_at') - F('assigned_at'),
                output_field=FloatField()
            )
        ).filter(completion_time__lte=value*3600)  # Convert hours to seconds



class IncidentVolunteerFilter(django_filters.FilterSet):
    distance = django_filters.NumberFilter(method='filter_by_distance')
    hours_min = django_filters.NumberFilter(
        field_name='hours_contributed',
        lookup_expr='gte'
    )
    hours_max = django_filters.NumberFilter(
        field_name='hours_contributed',
        lookup_expr='lte'
    )
    skill_match = django_filters.BooleanFilter(method='filter_skill_match')
    availability = django_filters.BooleanFilter(method='filter_availability')

    class Meta:
        model = IncidentVolunteer
        fields = {
            'incident': ['exact'],
            'volunteer': ['exact'],
            'assigned_at': ['gte', 'lte'],
            'completed_at': ['isnull'],
        }

    def filter_by_distance(self, queryset, name, value):
        if not self.request or not self.request.user.volunteer.preferred_location:
            return queryset
        
        # user_location = self.request.user.volunteer.preferred_location
        # return queryset.filter(
        #     incident__location__distance_lte=(
        #         user_location,
        #         D(km=value)
        #     )
        # ).annotate(
        #     distance=Distance('incident__location', user_location)
        # ).order_by('distance')

    def filter_skill_match(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            incident__required_skills__in=F('volunteer__skills')
        ).distinct()

    def filter_availability(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            volunteer__is_available=True,
            volunteer__availability__contains=self.request.GET.get('time_slot', '')
        )



class IncidentFilter(django_filters.FilterSet):
    # Standard filters
    status = django_filters.ChoiceFilter(choices=Incident.STATUS_CHOICES)
    priority = django_filters.ChoiceFilter(choices=Incident.PRIORITY_CHOICES)
    category = django_filters.ModelChoiceFilter(queryset=IncidentCategory.objects.all())
    is_sensitive = django_filters.BooleanFilter()
    
    # Additional custom filters
    severity_level = django_filters.NumberFilter(
        field_name='category__severity_level',
        lookup_expr='exact'
    )
    severity_level_gte = django_filters.NumberFilter(
        field_name='category__severity_level',
        lookup_expr='gte'
    )
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte'
    )
    requires_professional = django_filters.BooleanFilter(
        field_name='category__requires_professional_responder'
    )
    assigned_to_me = django_filters.BooleanFilter(method='filter_assigned_to_me')
    reported_by_me = django_filters.BooleanFilter(method='filter_reported_by_me')
    my_incidents = django_filters.BooleanFilter(method='filter_my_incidents')

    def filter_assigned_to_me(self, queryset, name, value):
        if not value:
            return queryset
            
        user = self.request.user
        if user.has_role('RESPONDER'):
            return queryset.filter(assigned_responders=user.responder)
        elif user.has_role('VOLUNTEER'):
            return queryset.filter(assigned_volunteers=user.volunteer)  # This is cleaner!
        return queryset

    def filter_reported_by_me(self, queryset, name, value):
        if not value:
            return queryset
        if self.request.user.has_role('REPORTER'):
            return queryset.filter(reporter=self.request.user.reporter)  # This is cleaner!
        return queryset
    
    def filter_my_incidents(self, queryset, name, value):
        if not value:
            return queryset
            
        user = self.request.user
        conditions = Q()
        
        if user.has_role('RESPONDER'):
            conditions |= Q(assigned_responders=user.responder)
        if user.has_role('REPORTER'):
            conditions |= Q(reporter=user.reporter)
        if user.has_role('VOLUNTEER'):
            conditions |= Q(assigned_volunteers=user.volunteer)
            
        return queryset.filter(conditions)

    class Meta:
        model = Incident
        fields = [
            'status', 
            'priority', 
            'category', 
            'is_sensitive',
            'severity_level',
            'severity_level_gte',
            'created_after',
            'created_before',
            'requires_professional',
            'assigned_to_me',
            'reported_by_me',
            'my_incidents'
        ]


from django_filters import rest_framework as filters
from django.db.models import Q, F
from django.utils import timezone

class IncidentResourceFilter(filters.FilterSet):
    """Advanced filter for IncidentResource management"""
    
    # Basic filters
    status = filters.ChoiceFilter(choices=IncidentResource.STATUS_CHOICES)
    return_status = filters.ChoiceFilter(choices=IncidentResource.RETURN_STATUS_CHOICES)
    
    priority = filters.ChoiceFilter(choices=Incident.PRIORITY_CHOICES)
    
    # Date range filters
    requested_after = filters.DateTimeFilter(
        field_name='requested_at',
        lookup_expr='gte'
    )
    requested_before = filters.DateTimeFilter(
        field_name='requested_at',
        lookup_expr='lte'
    )
    allocated_after = filters.DateTimeFilter(
        field_name='allocated_at',
        lookup_expr='gte'
    )
    allocated_before = filters.DateTimeFilter(
        field_name='allocated_at',
        lookup_expr='lte'
    )
    
    # Resource allocation filters
    has_shortage = filters.BooleanFilter(method='filter_shortage')
    allocation_percentage = filters.NumberFilter(method='filter_allocation_percentage')
    allocation_percentage_gte = filters.NumberFilter(method='filter_allocation_percentage_gte')
    allocation_percentage_lte = filters.NumberFilter(method='filter_allocation_percentage_lte')
    
    # Status-based filters
    is_overdue = filters.BooleanFilter(method='filter_overdue')
    is_expiring_soon = filters.BooleanFilter(method='filter_expiring_soon')
    is_fully_allocated = filters.BooleanFilter(method='filter_fully_allocated')
    needs_attention = filters.BooleanFilter(method='filter_needs_attention')
    
    # User-based filters
    requested_by = filters.ModelChoiceFilter(queryset=User.objects.all())
    return_verified_by = filters.ModelChoiceFilter(queryset=User.objects.all())
    allocated_by = filters.ModelChoiceFilter(queryset=User.objects.all())
    my_requests = filters.BooleanFilter(method='filter_my_requests')
    my_allocations = filters.BooleanFilter(method='filter_my_allocations')
    
    # Resource type filters
    resource_type = filters.CharFilter(field_name='resource__type')
    resource_category = filters.CharFilter(field_name='resource__category')
    
    # Incident-based filters
    incident_status = filters.ChoiceFilter(
        field_name='incident__status',
        choices=Incident.STATUS_CHOICES
    )
    incident_priority = filters.ChoiceFilter(
        field_name='incident__priority',
        choices=Incident.PRIORITY_CHOICES
    )

    def filter_shortage(self, queryset, name, value):
        if value:
            return queryset.filter(quantity_requested__gt=F('quantity_allocated'))
        return queryset

    def filter_allocation_percentage(self, queryset, name, value):
        return queryset.annotate(
            alloc_percentage=(F('quantity_allocated') * 100.0) / F('quantity_requested')
        ).filter(alloc_percentage=value)

    def filter_allocation_percentage_gte(self, queryset, name, value):
        return queryset.annotate(
            alloc_percentage=(F('quantity_allocated') * 100.0) / F('quantity_requested')
        ).filter(alloc_percentage__gte=value)

    def filter_allocation_percentage_lte(self, queryset, name, value):
        return queryset.annotate(
            alloc_percentage=(F('quantity_allocated') * 100.0) / F('quantity_requested')
        ).filter(alloc_percentage__lte=value)

    def filter_overdue(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            Q(expected_return_date__lt=timezone.now()) &
            Q(status='FULLY_ALLOCATED') &
            Q(returned_at__isnull=True)
        )

    def filter_expiring_soon(self, queryset, name, value):
        if not value:
            return queryset
        threshold = timezone.now() + timezone.timedelta(days=1)
        return queryset.filter(
            Q(expected_return_date__lte=threshold) &
            Q(expected_return_date__gt=timezone.now()) &
            Q(status='FULLY_ALLOCATED') &
            Q(returned_at__isnull=True)
        )

    def filter_fully_allocated(self, queryset, name, value):
        if value:
            return queryset.filter(quantity_allocated__gte=F('quantity_requested'))
        return queryset.filter(quantity_allocated__lt=F('quantity_requested'))

    def filter_needs_attention(self, queryset, name, value):
        """Filter resources that need immediate attention"""
        if not value:
            return queryset
            
        now = timezone.now()
        return queryset.filter(
            Q(status__in=['REQUESTED', 'PARTIALLY_ALLOCATED']) |
            (Q(expected_return_date__lt=now) & Q(returned_at__isnull=True)) |
            Q(incident__priority__in=['HIGH', 'CRITICAL', 'EMERGENCY'])
        )

    def filter_my_requests(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(requested_by=self.request.user)

    def filter_my_allocations(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(allocated_by=self.request.user)

    class Meta:
        model = IncidentResource
        fields = {
            'incident': ['exact'],
            'resource': ['exact'],
            'quantity_requested': ['exact', 'gte', 'lte'],
            'quantity_allocated': ['exact', 'gte', 'lte'],
        }
