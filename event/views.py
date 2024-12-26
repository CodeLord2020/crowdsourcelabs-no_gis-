from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Event, EventCategory, EventResourceRequirement, EventVolunteer, EventTag
)
from .serializers import (
    EventSerializer, EventCategorySerializer, EventResourceRequirementSerializer,
    EventVolunteerSerializer, EventTagSerializer
)
from .filters import EventFilterSet, EventVolunteerFilterSet
from django.utils import timezone



class EventTagViewSet(viewsets.ModelViewSet):
    queryset = EventTag.objects.all()
    serializer_class = EventTagSerializer
    permission_classes = [permissions.IsAuthenticated]


class EventCategoryViewSet(viewsets.ModelViewSet):
    queryset = EventCategory.objects.all()
    serializer_class = EventCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = EventFilterSet


    def get_queryset(self):
        user = self.request.user
        if user.has_role('ADMIN'):
            return self.queryset
        else:
            return self.queryset.filter(
                Q(organizer=user) |
                Q(coordinators__in=[user]) |
                Q(event_volunteers__volunteer__user=user)
            ).distinct()
        
        
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = serializer.save()

        resource_requirements = request.data.get('resource_requirements', [])
        for req in resource_requirements:
            EventResourceRequirement.objects.create(
                event=event,
                resource_id=req['resource'],
                quantity_required=req['quantity_required'],
                priority=req['priority'],
                notes=req.get('notes', '')
            )

        # #send mail to admins about new event
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    

    @action(detail=True, methods=['post'])
    def volunteer(self, request, pk=None):
        event = self.get_object()
        if request.user.has_role('VOLUNTEER'):
            volunteer = request.user.volunteer
            if event.is_registration_open:
                EventVolunteer.objects.create(event=event, volunteer=volunteer)
                # #send mail to volunteer about signup
                return Response({'message': 'Volunteer signup successful'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'error': 'Event registration is closed'}, status=status.HTTP_400_BAD_REQUEST)
        
            return Response({'error': 'You have to be registered as a volunteer'}, status=status.HTTP_400_BAD_REQUEST)
        

    @action(detail=True, methods=['post'])
    def check_in(self, request, pk=None):
        event_volunteer = EventVolunteer.objects.get(
            event_id=pk,
            volunteer__user=request.user
        )
        if event_volunteer.can_check_in:
            event_volunteer.check_in_time = timezone.now()
            event_volunteer.save()
            # #send notification to event coordinators about volunteer check-in
            return Response({'message': 'Check-in successful'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Cannot check in at this time'}, status=status.HTTP_400_BAD_REQUEST)


    @action(detail=True, methods=['post'])
    def check_out(self, request, pk=None):
        event_volunteer = EventVolunteer.objects.get(
            event_id=pk,
            volunteer__user=request.user
        )
        if event_volunteer.check_in_time:
            event_volunteer.check_out_time = timezone.now()
            event_volunteer.save()
            # #send notification to event coordinators about volunteer check-out
            return Response({'message': 'Check-out successful'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'You must check in before checking out'}, status=status.HTTP_400_BAD_REQUEST)




class EventResourceRequirementViewSet(viewsets.ModelViewSet):
    queryset = EventResourceRequirement.objects.all()
    serializer_class = EventResourceRequirementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        else:
            return self.queryset.filter(
                Q(event__organizer=user) |
                Q(event__coordinators__in=[user])
            ).distinct()
        


class EventVolunteerViewSet(viewsets.ModelViewSet):
    queryset = EventVolunteer.objects.all()
    serializer_class = EventVolunteerSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = EventVolunteerFilterSet

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        else:
            return self.queryset.filter(
                Q(volunteer__user=user) |
                Q(event__organizer=user) |
                Q(event__coordinators__in=[user])
            ).distinct()
        

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event_volunteer = serializer.save()

        # Update event volunteer count
        event_volunteer.event.current_volunteers += 1
        event_volunteer.event.save()

        # #send mail to volunteer about signup

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        if instance.status == 'APPROVED' and serializer.validated_data['status'] != 'APPROVED':
            instance.event.current_volunteers -= 1
            instance.event.save()

        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def perform_destroy(self, instance):
        if instance.status == 'APPROVED':
            instance.event.current_volunteers -= 1
            instance.event.save()
        instance.delete()


    @action(detail=False, methods=['get'])
    def my_signups(self, request):
        queryset = self.filter_queryset(self.get_queryset().filter(volunteer__user=request.user))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)