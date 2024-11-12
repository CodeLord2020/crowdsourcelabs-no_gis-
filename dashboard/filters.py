from django.contrib.gis.measure import D
from django.db.models import F, ExpressionWrapper, DurationField
from django.utils import timezone
from datetime import datetime, timedelta
from django_filters import rest_framework as filters
from incident.models import Incident




class DashboardIncidentFilter(filters.FilterSet):
    date_range = filters.ChoiceFilter(
        choices=[
            ('today', 'Today'),
            ('week', 'This Week'),
            ('month', 'This Month'),
            ('quarter', 'This Quarter'),
            ('year', 'This Year'),
        ],
        method='filter_by_date_range'
    )
    severity_level = filters.NumberFilter(field_name='category__severity_level')
    response_time_gt = filters.NumberFilter(method='filter_by_response_time')
    location_within = filters.NumberFilter(method='filter_by_distance')
    reporter_credibility = filters.NumberFilter(
        field_name='reporter__credibility_score',
        lookup_expr='gte'
    )
    
    def filter_by_date_range(self, queryset, name, value):
        today = datetime.now().date()
        date_ranges = {
            'today': (today, today + timedelta(days=1)),
            'week': (today - timedelta(days=today.weekday()), today + timedelta(days=7)),
            'month': (today.replace(day=1), (today.replace(day=1) + timedelta(days=32)).replace(day=1)),
            'quarter': (today.replace(day=1, month=(today.month - 1) // 3 * 3 + 1),
                       today.replace(day=1, month=((today.month - 1) // 3 + 1) * 3 + 1)),
            'year': (today.replace(month=1, day=1),
                    today.replace(month=12, day=31))
        }
        start_date, end_date = date_ranges.get(value, (None, None))
        if start_date and end_date:
            return queryset.filter(created_at__range=[start_date, end_date])
        return queryset

    def filter_by_response_time(self, queryset, name, value):
        return queryset.annotate(
            response_time=ExpressionWrapper(
                F('first_response_at') - F('created_at'),
                output_field=DurationField()
            )
        ).filter(response_time__gt=timedelta(minutes=value))

    def filter_by_distance(self, queryset, name, value):
        user_location = self.request.user.get_location()
        if user_location:
            return queryset.filter(
                location__distance_lte=(user_location, D(km=value))
            )
        return queryset

    class Meta:
        model = Incident
        fields = ['status', 'priority', 'category', 'is_sensitive']
