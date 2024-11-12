from django.db.models import Q, Count
from django_filters import rest_framework as filters
from .models import Role, UserRole
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta

User = get_user_model()

class UserFilter(filters.FilterSet):
    # Basic filters
    email = filters.CharFilter(lookup_expr='iexact')
    first_name = filters.CharFilter(lookup_expr='icontains')
    last_name = filters.CharFilter(lookup_expr='icontains')
    is_active = filters.BooleanFilter()
    is_verified = filters.BooleanFilter()
    
    # Date range filters
    created_after = filters.DateTimeFilter(
        field_name='date_joined',
        lookup_expr='gte'
    )
    created_before = filters.DateTimeFilter(
        field_name='date_joined',
        lookup_expr='lte'
    )
    
    # Age range filters
    min_age = filters.NumberFilter(method='filter_min_age')
    max_age = filters.NumberFilter(method='filter_max_age')
    
    # Activity filters
    last_active_after = filters.DateTimeFilter(
        field_name='last_active',
        lookup_expr='gte'
    )
    is_online = filters.BooleanFilter(method='filter_online_status')
    inactive_days = filters.NumberFilter(method='filter_inactive_days')
    
    # Role-based filters
    has_role = filters.CharFilter(method='filter_has_role')
    has_any_role = filters.MultipleChoiceFilter(
        choices=Role.ROLE_CHOICES,
        method='filter_has_any_role'
    )
    has_all_roles = filters.MultipleChoiceFilter(
        choices=Role.ROLE_CHOICES,
        method='filter_has_all_roles'
    )
    active_roles_only = filters.BooleanFilter(
        method='filter_active_roles'
    )
    
    # Phone number filters
    has_phone = filters.BooleanFilter(
        field_name='phone_number',
        lookup_expr='isnull',
        exclude=True
    )
    has_emergency_contact = filters.BooleanFilter(
        method='filter_has_emergency_contact'
    )
    
    # Profile completeness
    is_profile_complete = filters.BooleanFilter(
        method='filter_profile_complete'
    )
    has_profile_picture = filters.BooleanFilter(
        field_name='profile_picture',
        lookup_expr='isnull',
        exclude=True
    )

    class Meta:
        model = User
        fields = {
            'email': ['exact', 'icontains'],
            'first_name': ['exact', 'icontains'],
            'last_name': ['exact', 'icontains'],
            'is_active': ['exact'],
            'is_verified': ['exact'],
            'date_joined': ['exact', 'lt', 'gt'],
            'last_active': ['exact', 'lt', 'gt'],
        }

    def filter_min_age(self, queryset, name, value):
        today = timezone.now().date()
        date_of_birth = today - timedelta(days=value*365)
        return queryset.filter(date_of_birth__lte=date_of_birth)

    def filter_max_age(self, queryset, name, value):
        today = timezone.now().date()
        date_of_birth = today - timedelta(days=value*365)
        return queryset.filter(date_of_birth__gte=date_of_birth)

    def filter_online_status(self, queryset, name, value):
        time_threshold = timezone.now() - timedelta(minutes=5)
        if value:
            return queryset.filter(last_active__gte=time_threshold)
        return queryset.filter(
            Q(last_active__lt=time_threshold) | Q(last_active__isnull=True)
        )

    def filter_inactive_days(self, queryset, name, value):
        inactive_threshold = timezone.now() - timedelta(days=value)
        return queryset.filter(last_active__lt=inactive_threshold)

    def filter_has_role(self, queryset, name, value):
        return queryset.filter(
            user_roles__role__role_type=value,
            user_roles__is_active=True
        )

    def filter_has_any_role(self, queryset, name, value):
        return queryset.filter(
            user_roles__role__role_type__in=value,
            user_roles__is_active=True
        ).distinct()

    def filter_has_all_roles(self, queryset, name, value):
        for role in value:
            queryset = queryset.filter(
                user_roles__role__role_type=role,
                user_roles__is_active=True
            )
        return queryset.distinct()

    def filter_active_roles(self, queryset, name, value):
        if value:
            return queryset.filter(user_roles__is_active=True).distinct()
        return queryset

    def filter_has_emergency_contact(self, queryset, name, value):
        if value:
            return queryset.exclude(
                Q(emergency_contact='') & Q(emergency_phone='')
            )
        return queryset.filter(
            emergency_contact='',
            emergency_phone=''
        )

    def filter_profile_complete(self, queryset, name, value):
        if value:
            return queryset.exclude(
                Q(phone_number='') |
                Q(date_of_birth__isnull=True) |
                Q(bio='') |
                Q(profile_picture__isnull=True)
            )
        return queryset.filter(
            Q(phone_number='') |
            Q(date_of_birth__isnull=True) |
            Q(bio='') |
            Q(profile_picture__isnull=True)
        )

    @property
    def qs(self):
        """
        Add custom annotations to the queryset before filtering
        """
        queryset = super().qs
        return queryset.select_related('profile_picture').prefetch_related('user_roles')

class RoleFilter(filters.FilterSet):
    created_after = filters.DateTimeFilter(field_name="created_at", lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name="created_at", lookup_expr='lte')
    has_users = filters.BooleanFilter(method='filter_has_users')

    class Meta:
        model = Role
        fields = {
            'role_type': ['exact', 'in'],
        }

    def filter_has_users(self, queryset, name, value):
        return queryset.annotate(
            user_count=Count('userrole')
        ).filter(user_count__gt=0) if value else queryset


class UserRoleFilter(filters.FilterSet):
    assigned_after = filters.DateTimeFilter(field_name="assigned_at", lookup_expr='gte')
    assigned_before = filters.DateTimeFilter(field_name="assigned_at", lookup_expr='lte')
    assigned_by_username = filters.CharFilter(
        field_name="assigned_by__username",
        lookup_expr='iexact'
    )
    role_type = filters.ChoiceFilter(
        field_name="role__role_type",
        choices=Role.ROLE_CHOICES
    )

    class Meta:
        model = UserRole
        fields = {
            'is_active': ['exact'],
            'user': ['exact'],
            'role': ['exact'],
        }
