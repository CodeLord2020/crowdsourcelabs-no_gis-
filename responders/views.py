from django.shortcuts import render
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import  DjangoFilterBackend
from accounts.permissions import (
    AdminPermission, SuperAdminPermission,
    VolunteerPermission, ReporterPermission, ResponderPermission
)
from datetime import timedelta
from django.utils import timezone
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from .models import (
    Responder,
)
from .serializers import (
    ResponderSerializer,
)

from django.contrib.auth import get_user_model
User = get_user_model()



class ResponderViewSet(viewsets.ModelViewSet):
    queryset = Responder.objects.all()
    serializer_class = ResponderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_on_duty', 'organization']
    search_fields = ['user__first_name', 'user__last_name', 'certification_number']

    def get_queryset(self):
        queryset = Responder.objects.all()
        
        if self.action == 'list':
            # Filter active and on-duty responders by default
            queryset = queryset.filter(
                user__is_active=True,
                is_certified=True
            )
            
            # Location-based filtering
            lat = self.request.query_params.get('latitude')
            lon = self.request.query_params.get('longitude')

            if lat and lon:
                point = Point(float(lon), float(lat), srid=4326)
                queryset = queryset.filter(
                    user__location__location__distance_lte=(point, D(km=10))
                ).annotate(
                    distance=Distance('user__location__location', point)
                ).order_by('distance')
            
             # Specialization filtering
            specializations = self.request.query_params.getlist('specializations')
            if specializations:
                queryset = queryset.filter(
                    specializations__id__in=specializations
                )

        return queryset

    @action(detail=True, methods=['post'])
    def toggle_duty_status(self, request, pk=None):
        responder = self.get_object()
        responder.is_on_duty = not responder.is_on_duty
        responder.save()
        return Response(ResponderSerializer(responder).data)
    
    
    @action(detail=False, methods=['get'])
    def expiring_certifications(self, request):
        # Get responders whose certifications expire within 30 days
        threshold = timezone.now().date() + timedelta(days=30)
        responders = Responder.objects.filter(
            certification_expiry__lte=threshold,
            certification_expiry__gt=timezone.now().date()
        ).order_by('certification_expiry')
        return Response(ResponderSerializer(responders, many=True).data)
    

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q
from .models import Specialization, Responder
from .serializers import SpecializationSerializer
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle



class SpecializationViewSet(viewsets.ModelViewSet):
    """
    A sophisticated viewset for managing Specializations.
    """
    queryset = Specialization.objects.annotate(
        responder_count=Count('responder')
    ).order_by('-responder_count')
    serializer_class = SpecializationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['required_certification']
    search_fields = ['name', 'description']
    ordering_fields = ['responder_count', 'name']

    def get_queryset(self):
        """
        Overrides to add caching and optimize query performance.
        """
        # cached_queryset = cache.get('specializations_queryset')
        # if cached_queryset:
        #     return cached_queryset
        
        queryset = super().get_queryset()
        # cache.set('specializations_queryset', queryset, timeout=60*10)  # Cache for 10 minutes
        return queryset

    def perform_create(self, serializer):
        """
        Custom save logic on create.
        """
        specialization = serializer.save()
        # Additional post-save logic here if needed
        return specialization

    def perform_update(self, serializer):
        """
        Custom update logic.
        """
        specialization = serializer.save()
        # Additional post-update logic here if needed
        return specialization

    def perform_destroy(self, instance):
        """
        Custom deletion logic.
        """
        # Additional pre-delete logic here if needed
        instance.delete()

    @action(detail=True, methods=['get'], url_path='responders')
    def responders(self, request, pk=None):
        """
        Custom action to list responders with this specialization.
        """
        specialization = self.get_object()
        responders = specialization.responder_set.all()
        responder_data = [{"id": responder.id, "name": responder.user.full_name} for responder in responders]
        return Response({"specialization": specialization.name, "responders": responder_data})

    @action(detail=True, methods=['get'], url_path='certified-uncertified-count')
    def certified_uncertified_count(self, request, pk=None):
        """
        Custom action to get the count of certified and uncertified responders for a specialization.
        """
        specialization = self.get_object()
        certified_count = specialization.responder_set.filter(
            certification_expiry__gt=timezone.now().date()
        ).count()
        uncertified_count = specialization.responder_set.filter(
            certification_expiry__lte=timezone.now().date()
        ).count()
        
        return Response({
            "specialization": specialization.name,
            "certified_count": certified_count,
            "uncertified_count": uncertified_count
        })

    def get_serializer_context(self):
        """
        Add extra context if needed for serializers.
        """
        context = super().get_serializer_context()
        context.update({
            "request_user": self.request.user,
            "view_name": self.__class__.__name__,
        })
        return context

    def get_throttles(self):
        """
        Custom throttling based on action if needed.
        """
        if self.action == 'responders':
            return [UserRateThrottle()]
        return super().get_throttles()
    
    def get_permissions(self):
        """
        Custom permission checks based on actions.
        """
        if self.action in ['create', 'update', 'destroy']:
            self.permission_classes = [AdminPermission]
        else:
            self.permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        return super().get_permissions()

    def list(self, request, *args, **kwargs):
        """
        Override list to include extra metadata if needed.
        """
        response = super().list(request, *args, **kwargs)
        response.data['metadata'] = {
            'total_specializations': self.queryset.count(),
            'ordering_options': self.ordering_fields,
            'filters': self.filterset_fields
        }
        return response

