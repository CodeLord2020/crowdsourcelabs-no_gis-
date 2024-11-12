from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Avg, Sum, F, Q, Max, ExpressionWrapper, DurationField
from django.utils import timezone
from datetime import datetime, timedelta
from accounts.permissions import AdminPermission, SuperAdminPermission
from .filters import DashboardIncidentFilter
from incident.models import Incident, IncidentResource
from volunteer.models import Volunteer
from cddpresources.models import Resource, ResourceDonation
from event.models import Event, EventVolunteer
from reporters.models import Reporter
from cddpresources.serializers import ResourceSerializer, ResourceDonationSerializer
from event.serializers import EventSerializer, EventVolunteerSerializer



class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [AdminPermission|SuperAdminPermission]
    filterset_class = DashboardIncidentFilter

    @action(detail=False, methods=['get'])
    def incident_overview(self, request):
        incidents = Incident.objects.all()
        if request.user.has_role('RESPONDER'):
            incidents = incidents.filter(assigned_responders=request.user.responder)

        filtered_incidents = self.filterset_class(
            request.GET,
            queryset=incidents,
            request=request
        ).qs

        return Response({
            'total_incidents': filtered_incidents.count(),
            'incidents_by_status': self._get_incidents_by_status(filtered_incidents),
            'incidents_by_priority': self._get_incidents_by_priority(filtered_incidents),
            'response_metrics': self._get_response_metrics(filtered_incidents),
            'resource_utilization': self._get_resource_utilization(),
            'volunteer_metrics': self._get_volunteer_metrics(),
            'reporter_metrics': self._get_reporter_metrics()
        })
    
    @action(detail=False, methods=['get'])
    def resource_overview(self, request):
        user = request.user

        resource_count = Resource.objects.count()
        resource_value = Resource.objects.aggregate(total_value=Sum('cost_per_unit'))['total_value'] or 0

        if user.is_staff:
            event_count = Event.objects.count()
            event_volunteers = EventVolunteer.objects.count()
            event_hours = EventVolunteer.objects.aggregate(total_hours=Sum('hours_logged'))['total_hours'] or 0
        else:
            event_count = Event.objects.filter(
                Q(organizer=user) | Q(coordinators__in=[user]) | Q(event_volunteers__volunteer__user=user)
            ).distinct().count()
            event_volunteers = EventVolunteer.objects.filter(volunteer__user=user).count()
            event_hours = EventVolunteer.objects.filter(volunteer__user=user).aggregate(total_hours=Sum('hours_logged'))['total_hours'] or 0

        donation_count = ResourceDonation.objects.count()
        donation_value = ResourceDonation.objects.aggregate(total_value=Sum('monetary_value'))['total_value'] or 0

        return Response({
            'resource_count': resource_count,
            'resource_value': resource_value,
            'event_count': event_count,
            'event_volunteers': event_volunteers,
            'event_hours': event_hours,
            'donation_count': donation_count,
            'donation_value': donation_value
        })

    @action(detail=False, methods=['get'])
    def performance_metrics(self, request):
        return Response({
            'average_response_times': self._get_average_response_times(),
            'resolution_rates': self._get_resolution_rates(),
            'resource_efficiency': self._get_resource_efficiency(),
            'volunteer_effectiveness': self._get_volunteer_effectiveness(),
            'reporter_reliability': self._get_reporter_reliability()
        })
    
    @action(detail=False, methods=['get'])
    def top_resources(self, request):
        top_resources = Resource.objects.order_by('-quantity_available')[:10]
        serializer = ResourceSerializer(top_resources, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming_events(self, request):
        upcoming_events = Event.objects.filter(start_date__gt=timezone.now()).order_by('start_date')[:10]
        serializer = EventSerializer(upcoming_events, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_events(self, request):
        user = request.user
        my_events = Event.objects.filter(
            Q(organizer=user) | Q(coordinators__in=[user]) | Q(event_volunteers__volunteer__user=user)
        ).distinct().order_by('-start_date')
        serializer = EventSerializer(my_events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_donations(self, request):
        user = request.user
        my_donations = ResourceDonation.objects.filter(donor=user).order_by('-donation_date')
        serializer = ResourceDonationSerializer(my_donations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_event_signups(self, request):
        user = request.user
        my_signups = EventVolunteer.objects.filter(volunteer__user=user).order_by('-signup_date')
        serializer = EventVolunteerSerializer(my_signups, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def geographical_distribution(self, request):
        incidents = Incident.objects.all()
        return Response({
            'incident_clusters': self._get_incident_clusters(incidents),
            'resource_availability': self._get_resource_availability_map(),
            'response_coverage': self._get_response_coverage_map()
        })

    def _get_incidents_by_status(self, incidents):
        return incidents.values('status').annotate(
            count=Count('id'),
            avg_response_time=Avg('response_time')
        )

    def _get_response_metrics(self, incidents):
        return {
            'average_response_time': incidents.exclude(
                status__in=['REPORTED', 'VERIFIED']
            ).aggregate(Avg('response_time'))['response_time__avg'],
            'overdue_incidents': incidents.filter(is_overdue=True).count(),
            'response_time_distribution': self._get_response_time_distribution(incidents)
        }

    def _get_resource_utilization(self):
        return IncidentResource.objects.values(
            'resource__name'
        ).annotate(
            total_allocated=Sum('quantity_allocated'),
            utilization_rate=F('quantity_allocated') * 100.0 / F('quantity_requested')
        )

    def _get_volunteer_metrics(self):
        return Volunteer.objects.aggregate(
            total_active=Count('id', filter=Q(is_available=True)),
            average_rating=Avg('rating'),
            total_hours=Sum('verified_hours')
        )

    def _get_reporter_reliability(self):
        return Reporter.objects.values(
            'credibility_score'
        ).annotate(
            report_count=Count('id'),
            verification_rate=F('reports_verified') * 100.0 / F('reports_submitted')
        ).order_by('-credibility_score')

    def _get_response_time_distribution(self, incidents):
        ranges = [
            ('under_1h', timedelta(hours=1)),
            ('1h_to_3h', timedelta(hours=3)),
            ('3h_to_6h', timedelta(hours=6)),
            ('6h_to_12h', timedelta(hours=12)),
            ('over_12h', None)
        ]
        
        distribution = {}
        for label, threshold in ranges:
            if threshold:
                count = incidents.filter(response_time__lt=threshold.total_seconds()/60).count()
            else:
                count = incidents.filter(response_time__gte=ranges[-2][1].total_seconds()/60).count()
            distribution[label] = count
            
        return distribution

    def _get_incident_clusters(self, incidents):
        return incidents.values(
            'location'
        ).annotate(
            incident_count=Count('id'),
            avg_response_time=Avg('response_time'),
            resolution_rate=Count(
                'id',
                filter=Q(status__in=['RESOLVED', 'CLOSED'])
            ) * 100.0 / Count('id')
        )

    @action(detail=False, methods=['get'])
    def resource_forecast(self, request):
        """Predict resource needs based on historical data and current trends"""
        current_month = timezone.now().month
        historical_data = IncidentResource.objects.filter(
            incident__created_at__month=current_month
        ).values(
            'resource__name'
        ).annotate(
            avg_monthly_usage=Avg('quantity_requested'),
            peak_usage=Max('quantity_requested'),
            typical_duration=Avg(
                ExpressionWrapper(
                    F('returned_at') - F('allocated_at'),
                    output_field=DurationField()
                )
            )
        )
        
        return Response(historical_data)

    @action(detail=False, methods=['get'])
    def system_health(self, request):
        """Monitor system performance and resource utilization metrics"""
        now = timezone.now()
        hour_ago = now - timedelta(hours=1)
        
        return Response({
            'response_times': {
                'last_hour': Incident.objects.filter(
                    created_at__gte=hour_ago
                ).aggregate(
                    avg_response=Avg('response_time'),
                    max_response=Max('response_time')
                ),
                'error_rate': Incident.objects.filter(
                    status='INVALID',
                    created_at__gte=hour_ago
                ).count() / Incident.objects.filter(
                    created_at__gte=hour_ago
                ).count() * 100
            },
            'resource_availability': self._get_resource_availability(),
            'system_load': {
                'active_incidents': Incident.objects.exclude(
                    status__in=['RESOLVED', 'CLOSED', 'INVALID']
                ).count(),
                'pending_verifications': Incident.objects.filter(
                    status='REPORTED'
                ).count(),
                'resource_requests': IncidentResource.objects.filter(
                    status='REQUESTED'
                ).count()
            }
        })
