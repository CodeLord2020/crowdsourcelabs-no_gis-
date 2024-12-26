import django_filters
from .models import EventStatus, Event, EventCategory, EventPriority,EventVolunteer, EventTag
from volunteer.models import Volunteer
from django.db.models import Q



class EventFilterSet(django_filters.FilterSet):
    start_date = django_filters.DateTimeFilter(field_name='start_date', lookup_expr='gte')
    end_date = django_filters.DateTimeFilter(field_name='end_date', lookup_expr='lte')
    registration_deadline = django_filters.DateTimeFilter(field_name='registration_deadline', lookup_expr='lte')
    status = django_filters.MultipleChoiceFilter(choices=EventStatus.choices)
    priority = django_filters.MultipleChoiceFilter(choices=EventPriority.choices)
    category = django_filters.ModelMultipleChoiceFilter(queryset=EventCategory.objects.all())
    tags = django_filters.ModelMultipleChoiceFilter(queryset=EventTag.objects.all())
    is_featured = django_filters.BooleanFilter()
    is_virtual = django_filters.BooleanFilter()
    search = django_filters.CharFilter(method='search_filter')

    class Meta:
        model = Event
        fields = ['start_date', 'end_date', 'registration_deadline', 'status', 'priority', 'category', 'is_featured', 'is_virtual']

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(location_name__icontains=value)
        )

class EventVolunteerFilterSet(django_filters.FilterSet):
    event = django_filters.ModelChoiceFilter(queryset=Event.objects.all())
    volunteer = django_filters.ModelChoiceFilter(queryset=Volunteer.objects.all())
    status = django_filters.MultipleChoiceFilter(choices=EventVolunteer.status_choices)
    signup_date = django_filters.DateTimeFilter(field_name='signup_date', lookup_expr='gte')
    check_in_time = django_filters.DateTimeFilter(field_name='check_in_time', lookup_expr='gte')
    check_out_time = django_filters.DateTimeFilter(field_name='check_out_time', lookup_expr='gte')

    class Meta:
        model = EventVolunteer
        fields = ['event', 'volunteer', 'status', 'signup_date', 'check_in_time', 'check_out_time']