from django.shortcuts import render
from .models import ( Incident, IncidentAssignment,
                      IncidentCategory, Task, IncidentUpdate,
                        IncidentResource, IncidentVolunteer)
from .filters import TaskFilter, IncidentVolunteerFilter, IncidentAssignmentFilter, IncidentFilter, IncidentResourceFilter
from .serializers import (TaskSerializer, IncidentSerializer, IncidentResourceSerializer,
                          IncidentAssignmentSerializer, IncidentUpdateSerializer,
                          IncidentLocationSerializer, IncidentCategorySerializer)
from rest_framework import viewsets, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from accounts.permissions import AdminPermission, ResponderPermission, VolunteerPermission, ReporterPermission
from django.db.models import Q
from rest_framework.decorators import action
from rest_framework.response import Response
from volunteer.models import Volunteer
from django.utils import timezone
from django.db import transaction
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from cddp.tasks import(send_return_submission_notification, send_return_verification_notification,
                       send_overdue_reminder, send_allocation_notification, send_task_completion_notification,
                       send_task_assignment_notification, send_incident_status_notification,
                       send_responder_assignment_notification)
from django.urls import reverse
from responders.models import Responder



class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [AdminPermission|ResponderPermission|VolunteerPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filter_class = TaskFilter
    queryset = Task.objects.all()
    search_fields = ['title', 'description']
    ordering_fields = ['priority', 'due_date', 'created_at', 'status']

    from django.db.models import Q

    def get_queryset(self):
        user = self.request.user
        queryset = Task.objects.all()

        # Admins and users with explicit permission can view all tasks
        if user.has_perm('tasks.view_all_tasks'):
            return queryset

        # Initialize a Q object for filtering based on roles
        user_filters = Q()

        # If user is a responder, add filter for tasks in their assigned incidents
        if user.has_role('RESPONDER'):
            user_filters |= Q(incident__assigned_responders=user)

        # If user is a volunteer, add filter for tasks they’re eligible for
        if user.has_role('VOLUNTEER'):
            # Assumes there’s an IncidentVolunteer linking volunteers and incidents
            user_filters |= Q(
                incident__incidentvolunteer__volunteer=user,
                incident__incidentvolunteer__status='PENDING'
            ) | Q(
                status='PENDING',
                required_skills__in=user.volunteer.skills.all()
            )

        # Filter based on accumulated conditions or return an empty set if none match
        return queryset.filter(user_filters) if user_filters else Task.objects.none()

    @action(detail=True, methods=['post'])
    def assign_volunteer(self, request, pk=None):
        task = self.get_object()
        volunteer_id = request.data.get('volunteer_id')
        
        try:
            volunteer = Volunteer.objects.get(id=volunteer_id)
            
            # Check if volunteer has required skills
            missing_skills = set(task.required_skills.all()) - set(volunteer.skills.all())
            if missing_skills:
                return Response(
                    {
                        "detail": f"Volunteer missing required skills: {', '.join(s.name for s in missing_skills)}"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            task.assign_volunteer(volunteer)
            send_task_assignment_notification.delay(task.id, volunteer.id)

            return Response({"status": "assigned"})
        
        except Volunteer.DoesNotExist:
            return Response(
                {"detail": "Volunteer not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        task = self.get_object()
        new_status = request.data.get('status')
        completion_percentage = request.data.get('completion_percentage', 0)
        
        if new_status not in dict(Task.STATUS_CHOICES):
            return Response(
                {"detail": "Invalid status"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        task.status = new_status
        task.completion_percentage = completion_percentage
        task.save()

        with transaction.atomic():
            if new_status == 'COMPLETED':
                volunteers = task.get_volunteers()
                for volunteer in volunteers:
                    assignment = task.volunteers.through.objects.get(
                        task=task,
                        volunteer=volunteer
                    )
                    if not assignment.completed_at:
                        assignment.completed_at = timezone.now()
                        assignment.save()
                        
                        # Update volunteer metrics
                        if task.estimated_time:
                            volunteer.verified_hours += task.estimated_time / 60
                            volunteer.save()
            
                send_task_completion_notification.delay(task.id)
        
        return Response({"status": "completed"})
    
    @action(detail=False, methods=['get'])
    def available_tasks(self, request):
        if not request.user.has_role('VOLUNTEER'):
            return Response(
                {"detail": "Must be a volunteer to view available tasks"},
                status=status.HTTP_403_FORBIDDEN
            )

        volunteer = request.user.volunteer

        assigned_task_ids = IncidentVolunteer.objects.filter(
            volunteer=volunteer
        ).values_list('tasks', flat=True)

        tasks = Task.objects.filter(
            status='PENDING',
            required_skills__in=volunteer.skills.all()
        ).exclude(
            id__in=assigned_task_ids
        ).distinct()

        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)




        
class IncidentCategoryViewSet(viewsets.ModelViewSet):
    queryset = IncidentCategory.objects.all()
    serializer_class = IncidentCategorySerializer
    permission_classes = [AdminPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['severity_level', 'requires_verification', 'requires_professional_responder']
    search_fields = ['name', 'description']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'list':
            # Only return top-level categories by default
            return queryset.filter(parent_category__isnull=True)
        return queryset
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        category = self.get_object()
        stats = {
            'total_incidents': Incident.objects.filter(category=category).count(),
            'average_response_time': Incident.objects.filter(
                category=category
            ).exclude(
                status__in=['REPORTED', 'VERIFIED']
            ).aggregate(Avg('response_time'))['response_time__avg'],
            'resolution_rate': Incident.objects.filter(
                category=category,
                status__in=['RESOLVED', 'CLOSED']
            ).count() / Incident.objects.filter(category=category).count() * 100
            if Incident.objects.filter(category=category).exists() else 0
        }
        return Response(stats)



class IncidentViewSet(viewsets.ModelViewSet):
    serializer_class = IncidentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = IncidentFilter
    search_fields = ['title', 'description', 'address']
    permission_classes = [AdminPermission|ResponderPermission|ReporterPermission]

    # def def get_queryset(self):
    #     return super().get_queryset()  

    def get_queryset(self):
        user = self.request.user
        queryset = Incident.objects.all()

        # If user has permission to view all incidents, return unfiltered queryset
        if user.has_perm('incidents.view_all_incidents'):
            return queryset

        # Build filter conditions based on user's roles
        conditions = Q()
        
        # Add conditions for each role the user has
        if user.has_role('RESPONDER'):
            conditions |= Q(assigned_responders=user.responder) | Q(category__requires_professional_responder=True)
            
        if user.has_role('REPORTER'):
            conditions |= Q(reporter=user.reporter)
            
        if user.has_role('VOLUNTEER'):
            conditions |= Q(is_sensitive=False) | Q(assigned_volunteers=user.volunteer)
        
        # If user has no relevant roles, only show non-sensitive incidents
        if not conditions:
            conditions = Q(is_sensitive=False)
            
        return queryset.filter(conditions)
    

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        if not request.user.has_role('ADMIN'):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        incident = self.get_object()
        previous_status = incident.status
        incident.verified_by = request.user
        incident.verified_at = timezone.now()
        incident.status = 'VERIFIED'
        incident.save()
    
        send_incident_status_notification.delay(incident.id, previous_status, 'VERIFIED')

        return Response({"status": "verified"})
    
    @action(detail=True, methods=['post'])
    def assign_responder(self, request, pk=None):
        if not request.user.has_role('ADMIN'):
            return Response(
                {"detail": "Permission denied"},
                status=status.HTTP_403_FORBIDDEN
            )

        incident = self.get_object()
        responder_id = request.data.get('responder_id')
        role = request.data.get('role', 'PRIMARY')

        try:
            responder = Responder.objects.get(id=responder_id)
            incident.assign_responder(responder, role)

            # Send notification to the assigned responder
            send_responder_assignment_notification.delay(incident.id, responder.id)

            return Response({"status": "assigned"})
        except Responder.DoesNotExist:
            return Response(
                {"detail": "Responder not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
    @action(detail=True, methods=['post'])
    def respond_to_incident(self, request, pk=None):
        incident = self.get_object()
        responder = request.user.responder

        try:
            assignment = incident.incidentassignment_set.get(responder=responder)

            if assignment.accepted_at is None:
                assignment.accepted_at = timezone.now()
                assignment.save()

                incident.status = 'RESPONDING'
                incident.save()
                send_incident_status_notification.delay(
                    incident.id,
                    incident.status,
                    'RESPONDING'
                )

                return Response({"status": "responded"})
            else:
                return Response(
                    {"detail": "You have already responded to this incident"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except IncidentAssignment.DoesNotExist:
            return Response(
                {"detail": "You are not assigned to this incident"},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        

    @action(detail=True, methods=['post'])
    def direct_response(self, request, pk=None):
        incident = self.get_object()
        responder = request.user.responder

        try:
            incident.assign_responder(responder, 'PRIMARY')
            incident.status = 'RESPONDING'
            incident.save()

            # Send notification to other stakeholders
            send_incident_status_notification.delay(
                incident.id,
                incident.status,
                'RESPONDING'
            )

            return Response({"status": "responded"})
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        incident = self.get_object()
        updates = incident.incident_timeline.all()
        serializer = IncidentUpdateSerializer(updates, many=True)
        return Response(serializer.data)



class ResourceManagementViewSet(viewsets.ModelViewSet):
    queryset = IncidentResource.objects.all()
    serializer_class = IncidentResourceSerializer
    filterset_class = IncidentResourceFilter
    permission_classes = [AdminPermission|ResponderPermission]

    def perform_create(self, serializer):
        serializer.save(requested_by=self.request.user)

    @action(detail=False, methods=['get'])
    def resource_needs(self, request):
        resources = self.get_queryset().values(
            'resource__name',
            'resource__id',
            'priority'
        ).annotate(
            total_requested=Sum('quantity_requested'),
            total_allocated=Sum('quantity_allocated'),
            pending_requests=Count('id', filter=Q(status='REQUESTED')),
            shortage=F('total_requested') - F('total_allocated'),
            urgent_requests=Count('id', filter=Q(priority__in=['HIGH', 'CRITICAL', 'EMERGENCY'])),
            # avg_fulfillment_time=Avg(F('allocated_at') - F('requested_at'),
            #                        filter=Q(allocated_at__isnull=False))
        ).filter(shortage__gt=0)
        
        return Response(resources)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get resources that need to be returned soon"""
        threshold = timezone.now() + timezone.timedelta(days=1)
        resources = self.get_queryset().filter(
            status='FULLY_ALLOCATED',
            expected_return_date__lte=threshold,
            returned_at__isnull=True
        )
        serializer = self.get_serializer(resources, many=True)
        return Response(serializer.data)
    

    
    @action(detail=True, methods=['post'])
    def allocate(self, request, pk=None):
        resource = self.get_object()
        quantity = request.data.get('quantity', 0)
        expected_return_date = request.data.get('expected_return_date')
        
        if quantity > resource.pending_quantity:
            return Response(
                {"detail": "Allocation exceeds requested quantity"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        resource.quantity_allocated += quantity
        resource.allocated_at = timezone.now()
        resource.allocated_by = request.user

        if expected_return_date:
            resource.expected_return_date = expected_return_date
        resource.update_status()
        resource.save()
        
        # Trigger notifications
        send_allocation_notification.delay(resource.id)
        
        return Response(self.get_serializer(resource).data)
    

    

    @action(detail=True, methods=['post'])
    def submit_return(self, request, pk=None):
        """Submit a return request that needs verification"""
        with transaction.atomic():
            resource = self.get_object()
            quantity = request.data.get('quantity', resource.quantity_allocated)
            notes = request.data.get('notes', '')
            
            if quantity > resource.quantity_allocated:
                return Response(
                    {"detail": "Return quantity exceeds allocation"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if quantity < resource.quantity_allocated:
                # Handling partial return
                resource.return_status = 'SUBMITTED'
                resource.return_notes = notes
                resource.partial_returns.append({
                    'quantity': quantity,
                    'date': timezone.now().isoformat(),
                    'submitted_by': request.user.id,
                    'status': 'PENDING'
                })

            else:
                # Full return
                resource.return_status = 'SUBMITTED'
                resource.return_notes = notes
            
            resource.save()
            send_return_submission_notification.delay(resource.id, quantity)

            return Response(self.get_serializer(resource).data)
       

        
    @action(detail=True, methods=['post'])
    def verify_return(self, request, pk=None):
        """Verify a return request (only allocated_by or admin can verify)"""
        with transaction.atomic():
            resource = self.get_object()
            
            # Check permissions
            if not (request.user == resource.allocated_by or 
                   request.user.has_role('ADMIN')):
                return Response(
                    {"detail": "Only resource allocator or admin can verify returns"},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            verification_status = request.data.get('status', 'VERIFIED')
            quantity = request.data.get('quantity', resource.quantity_allocated)
            notes = request.data.get('notes', '')
            if verification_status == 'VERIFIED':
                resource.quantity_allocated -= quantity
                resource.returned_at = timezone.now()
                resource.return_verified_by = request.user
                resource.return_verified_at = timezone.now()

                if resource.quantity_allocated == 0:
                        resource.status = 'RETURNED'
                else:
                    resource.status = 'PARTIALLY_ALLOCATED'
                
            elif verification_status == 'REJECTED':
                resource.return_status = 'REJECTED'
                resource.return_notes = notes
            
            resource.save()

            # Notify requested_by about verification
            send_return_verification_notification.delay(resource.id, verification_status)
            
            return Response(self.get_serializer(resource).data)

    
    
    @action(detail=False, methods=['get'])
    def overdue_returns(self, request):
        """Get resources that are past their expected return date"""
        resources = self.get_queryset().filter(
            status='FULLY_ALLOCATED',
            expected_return_date__lt=timezone.now(),
            returned_at__isnull=True
        )
        serializer = self.get_serializer(resources, many=True)
        return Response(serializer.data)
    


    @action(detail=False, methods=['post'])
    def send_overdue_reminders(self, request):
        """Send reminder emails for overdue returns"""
        overdue_resources = self.get_queryset().filter(
            status='FULLY_ALLOCATED',
            expected_return_date__lt=timezone.now(),
            returned_at__isnull=True
        )
        
        for resource in overdue_resources:
            send_overdue_reminder.delay(resource.id) 
        return Response({
            "message": f"Sent reminders for {overdue_resources.count()} overdue resources"
        })
    


    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a resource request"""
        resource = self.get_object()
        if resource.quantity_allocated > 0:
            return Response(
                {"detail": "Cannot cancel request with allocated resources"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        resource.status = 'CANCELLED'
        resource.save()
        return Response(self.get_serializer(resource).data)



    

