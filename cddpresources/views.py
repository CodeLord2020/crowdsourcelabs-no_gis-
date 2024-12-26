from rest_framework import viewsets, permissions
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from .models import ResourceTag, ResourceType, Resource, ResourceDonation
from .serializers import (
    ResourceTagSerializer, ResourceTypeSerializer, ResourceSerializer,
    ResourceDonationSerializer
)
from rest_framework.decorators import action
from rest_framework.response import Response
from .filters import ResourceFilterSet, ResourceDonationFilterSet



class ResourceTagViewSet(viewsets.ModelViewSet):
    queryset = ResourceTag.objects.all()
    serializer_class = ResourceTagSerializer
    permission_classes = [permissions.IsAuthenticated]



class ResourceTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ResourceType.objects.all()
    serializer_class = ResourceTypeSerializer
    permission_classes = [permissions.IsAuthenticated]



class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ResourceFilterSet

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        else:
            return self.queryset.filter(
                Q(owner=user) |
                Q(manager=user)
            ).distinct()
        
        
    def perform_create(self, serializer):
        resource = serializer.save()
        # #send notification to resource manager about new resource
        return resource

    def perform_update(self, serializer):
        old_instance = self.get_object()
        new_instance = serializer.save()
        if old_instance.quantity_available != new_instance.quantity_available:
            # #send notification to resource manager about quantity change
            pass
        return new_instance
    

    @action(detail=True, methods=['post'])
    def allocate(self, request, pk=None):
        resource = self.get_object()
        quantity = request.data.get('quantity', 0)
        if quantity > resource.quantity_available_for_allocation:
            return Response(
                {'error': 'Requested quantity exceeds available quantity'},
                status=status.HTTP_400_BAD_REQUEST
            )
        resource.quantity_allocated += quantity
        resource.save()
        
        #send notification to resource manager about allocation
        return Response({'message': 'Resource allocated successfully'}, status=status.HTTP_200_OK)

    
    @action(detail=True, methods=['post'])
    def return_allocated(self, request, pk=None):
        resource = self.get_object()
        quantity = request.data.get('quantity', 0)
        if quantity > resource.quantity_allocated:
            return Response(
                {'error': 'Requested return quantity exceeds allocated quantity'},
                status=status.HTTP_400_BAD_REQUEST
            )
        resource.quantity_allocated -= quantity
        resource.save()
        # #send notification to resource manager about returned allocation
        return Response({'message': 'Allocated resources returned successfully'}, status=status.HTTP_200_OK)
    
    

class ResourceDonationViewSet(viewsets.ModelViewSet):
    queryset = ResourceDonation.objects.all()
    serializer_class = ResourceDonationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ResourceDonationFilterSet

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        else:
            return self.queryset.filter(
                Q(donor=user) |
                Q(resource__owner=user) |
                Q(resource__manager=user)
            ).distinct()

    def perform_create(self, serializer):
        donation = serializer.save()
        # #send notification to resource manager about new donation
        return donation

    def perform_update(self, serializer):
        old_instance = self.get_object()
        new_instance = serializer.save()
        if old_instance.quantity != new_instance.quantity:
            # #send notification to resource manager about donation quantity change
            pass
        return new_instance

    def perform_destroy(self, instance):
        # #send notification to resource manager about donation removal
        instance.delete()
