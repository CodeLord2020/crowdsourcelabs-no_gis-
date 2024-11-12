from rest_framework import serializers
from django.contrib.gis.geos import Point
from .models import ResourceTag, ResourceType, Resource, ResourceDonation
from accounts.models import User


class ResourceTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceTag
        fields = ('id', 'name', 'description')


class ResourceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceType
        fields = ('id', 'name', 'description')


class ResourceSerializer(serializers.ModelSerializer):
    resource_type = ResourceTypeSerializer(read_only=True)
    resource_type_id = serializers.PrimaryKeyRelatedField(
        queryset=ResourceType.objects.all(), source='resource_type', write_only=True
    )
    owner = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='owner'
    )
    manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='manager'
    )
    location = serializers.SerializerMethodField()
    tags = ResourceTagSerializer(many=True, read_only=True)

    class Meta:
        model = Resource
        fields = (
            'id', 'name', 'resource_type', 'resource_type_id', 'description',
            'minimum_quantity', 'reorder_point', 'quantity_available',
            'quantity_allocated', 'quantity_available_for_allocation',
            'needs_reorder', 'media', 'unit', 'expiry_date', 'location',
            'owner', 'manager', 'is_consumable', 'is_perishable',
            'is_sharable', 'cost_per_unit', 'tags'
        )

    def get_location(self, obj):
        if obj.location:
            return {
                'latitude': obj.location.y,
                'longitude': obj.location.x
            }
        return {}
    

class ResourceDonationSerializer(serializers.ModelSerializer):
    resource = serializers.PrimaryKeyRelatedField(queryset=Resource.objects.all())
    donor = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = ResourceDonation
        fields = (
            'id', 'resource', 'donor', 'quantity', 'donation_date',
            'monetary_value', 'is_anonymous', 'receipt_issued', 'notes'
        )
