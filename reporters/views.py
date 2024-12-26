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
from .models import (
    Reporter,
)

from .serializers import (
    ReporterSerializer,
)

from django.contrib.auth import get_user_model
User = get_user_model()

    

class ReporterViewSet(viewsets.ModelViewSet):
    queryset = Reporter.objects.all()
    serializer_class = ReporterSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['credibility_score', 'reports_submitted', 'reports_verified']

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), ReporterPermission()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()

         # Filter by minimum credibility score
        min_score = self.request.query_params.get('min_credibility_score')
        if min_score:
            queryset = queryset.filter(credibility_score__gte=float(min_score))
            
        # Filter by minimum verification rate
        min_rate = self.request.query_params.get('min_verification_rate')
        if min_rate:
            queryset = queryset.annotate(
                ver_rate=F('reports_verified') * 100.0 / F('reports_submitted')
            ).filter(ver_rate__gte=float(min_rate))
            
        return queryset

    @action(detail=True, methods=['post'])
    def verify_report(self, request, pk=None):
        if not request.user.has_role('ADMIN') and not request.user.has_role('SUPERADMIN'):
            return Response(
                {'detail': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        reporter = self.get_object()
        reporter.reports_verified += 1
        reporter.update_credibility_score()
        return Response(ReporterSerializer(reporter).data)

