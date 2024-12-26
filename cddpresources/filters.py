
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as django_filters
from .models import Resource, ResourceTag, ResourceType, ResourceDonation
from accounts.models import User



class ResourceFilterSet(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    resource_type = django_filters.ModelMultipleChoiceFilter(queryset=ResourceType.objects.all())
    tags = django_filters.ModelMultipleChoiceFilter(queryset=ResourceTag.objects.all())
    owner = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    manager = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    is_consumable = django_filters.BooleanFilter()
    is_perishable = django_filters.BooleanFilter()
    is_sharable = django_filters.BooleanFilter()
    minimum_quantity_gte = django_filters.NumberFilter(field_name='minimum_quantity', lookup_expr='gte')
    reorder_point_gte = django_filters.NumberFilter(field_name='reorder_point', lookup_expr='gte')
    quantity_available_gte = django_filters.NumberFilter(field_name='quantity_available', lookup_expr='gte')
    quantity_allocated_gte = django_filters.NumberFilter(field_name='quantity_allocated', lookup_expr='gte')
    cost_per_unit_gte = django_filters.NumberFilter(field_name='cost_per_unit', lookup_expr='gte')
    cost_per_unit_lte = django_filters.NumberFilter(field_name='cost_per_unit', lookup_expr='lte')
    expiry_date_gte = django_filters.DateFilter(field_name='expiry_date', lookup_expr='gte')
    expiry_date_lte = django_filters.DateFilter(field_name='expiry_date', lookup_expr='lte')

    class Meta:
        model = Resource
        fields = [
            'name', 'description', 'resource_type', 'tags',
            'owner', 'manager', 'is_consumable', 'is_perishable',
            'is_sharable', 'minimum_quantity', 'reorder_point',
            'quantity_available', 'quantity_allocated', 'cost_per_unit',
            'expiry_date'
        ]

class ResourceDonationFilterSet(django_filters.FilterSet):
    resource = django_filters.ModelChoiceFilter(queryset=Resource.objects.all())
    donor = django_filters.ModelChoiceFilter(queryset=User.objects.all())
    donation_date = django_filters.DateTimeFilter(field_name='donation_date', lookup_expr='gte')
    is_anonymous = django_filters.BooleanFilter()
    receipt_issued = django_filters.BooleanFilter()

    class Meta:
        model = ResourceDonation
        fields = ['resource', 'donor', 'donation_date', 'is_anonymous', 'receipt_issued']