from django.shortcuts import render
from rest_framework import viewsets, filters, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, inline_serializer
from drf_spectacular.types import OpenApiTypes

from accounts.permissions import (
    AdminPermission, SuperAdminPermission,
    VolunteerPermission, ReporterPermission, ResponderPermission
)
from .filters import SkillFilterSet, VolunteerSkillFilterSet, VolunteerFilter
from django.db.models import Avg, Count, Q,F
# from django.contrib.gis.geos import Point
# from .services import VolunteerLocationService
from .models import (
    Volunteer,
    VolunteerSkill,
    Skill,

)
from .serializers import (
    VolunteerSerializer,
    SkillSerializer,
    VolunteerSkillSerializer,
    VolunteerRatingSerializer,
)

from django.contrib.auth import get_user_model
User = get_user_model()
# Create your views here.



class VolunteerViewSet(viewsets.ModelViewSet):
    queryset = Volunteer.objects.all()
    serializer_class = VolunteerSerializer
    # permission_classes = [IsAuthenticated, VolunteerPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = VolunteerFilter
    search_fields = ['user__first_name', 'user__last_name', 'skills__name']
    ordering_fields = ['rating', 'verified_hours', 'created_at', 'distance']
    ordering = ['-rating']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [AdminPermission()]
    
    @extend_schema(
        summary="List all volunteers",
        parameters=[
            OpenApiParameter(
                name='min_rating',
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description='Minimum volunteer rating (1-5)'
            ),
            OpenApiParameter(
                name='max_rating',
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description='Maximum volunteer rating (1-5)'
            ),
            OpenApiParameter(
                name='min_verified_hours',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Minimum number of verified volunteer hours'
            ),
            OpenApiParameter(
                name='skills',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by skill'
            ),
            OpenApiParameter(
                name='skills_category',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by skill category'
            ),
            OpenApiParameter(
                name='multiple_skills',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by multiple skill IDs (comma-separated)'
            ),
            OpenApiParameter(
                name='min_proficiency',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Minimum skill proficiency level (1-5)'
            ),
            OpenApiParameter(
                name='max_proficiency',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Maximum skill proficiency level (1-5)'
            ),
            OpenApiParameter(
                name='proficiency_level',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Skill proficiency level (1-5)'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Order by field (prefix with - for descending)'
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = super().get_queryset().annotate(
            average_rating=Avg('volunteerrating__rating'),
            total_ratings=Count('volunteerrating')
        )
        # if self.action == 'list':
        #     # Filter active and available volunteers by default
        #     queryset = queryset.filter(
        #         user__is_active=True,
        #         is_available=True
        #     )
        return queryset
    
    @extend_schema(
        summary="Search volunteers by skills and availability",
        parameters=[
            OpenApiParameter(
                name='skills',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Skill IDs (comma-separated)'
            ),
            OpenApiParameter(
                name='min_proficiency',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Minimum skill proficiency level (1-5)'
            ),
            OpenApiParameter(
                name='availability_days',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Days of the week (comma-separated)'
            ),
        ]
    )
    @action(detail=False, methods=['GET'])
    def search_by_skills(self, request):
        queryset = self.get_queryset()
        
        skills = request.query_params.get('skills')
        min_proficiency = request.query_params.get('min_proficiency')
        availability_days = request.query_params.get('availability_days')

        if skills:
            skill_ids = [int(id) for id in skills.split(',')]
            skill_query = Q()
            for skill_id in skill_ids:
                skill_query &= Q(skills__id=skill_id)
            
            if min_proficiency:
                skill_query &= Q(volunteerskill__proficiency_level__gte=int(min_proficiency))
            
            queryset = queryset.filter(skill_query)

        if availability_days:
            days = availability_days.split(',')
            availability_query = Q()
            for day in days:
                availability_query |= Q(availability__contains={day.lower(): True})
            queryset = queryset.filter(availability_query)

        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    

    
    @extend_schema(
        summary="Toggle volunteer availability status",
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=True, methods=['post'])
    def toggle_availability(self, request, pk=None):
        volunteer = self.get_object()
        volunteer.is_available = not volunteer.is_available
        volunteer.save()
        return Response({
            'status': 'availability updated',
            'is_available': volunteer.is_available
        })
    

    @extend_schema(
        summary="Rate a volunteer",
        request=VolunteerRatingSerializer,
        responses={201: VolunteerRatingSerializer}
    )
    @action(detail=True, methods=['post'])
    def rate_volunteer(self, request, pk=None):
        volunteer = self.get_object()
        serializer = VolunteerRatingSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(
                volunteer=volunteer,
                rated_by=request.user
            )
            volunteer.update_rating()
            return Response(serializer.data)
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @extend_schema(
        summary="Find nearby volunteers",
        parameters=[
            OpenApiParameter(
                name='latitude',
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description='Latitude coordinate'
            ),
            OpenApiParameter(
                name='longitude',
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description='Longitude coordinate'
            ),
            OpenApiParameter(
                name='radius',
                type=OpenApiTypes.FLOAT,
                location=OpenApiParameter.QUERY,
                description='Search radius in kilometers',
                default=10.0
            ),
            OpenApiParameter(
                name='skills_required',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Required skills IDs (comma-separated)'
            ),
        ]
    )
    @action(detail=False, methods=['GET'])
    def find_nearby(self, request):

        pass
        # try:
        #     latitude = float(request.query_params.get('latitude'))
        #     longitude = float(request.query_params.get('longitude'))
        #     radius = float(request.query_params.get('radius', 10.0))
        #     point = Point(longitude, latitude, srid=4326)
            
        #     queryset = self.get_queryset().filter(
        #         is_available=True,
        #         preferred_location__distance_lte=(point, D(km=radius))
        #     ).annotate(
        #         distance=Distance('preferred_location', point)
        #     )

        #     skills_required = request.query_params.get('skills_required')
        #     if skills_required:
        #         skill_ids = [int(id) for id in skills_required.split(',')]
        #         queryset = queryset.filter(skills__id__in=skill_ids)

        #     queryset = queryset.order_by('distance')
            
        #     page = self.paginate_queryset(queryset)
        #     serializer = self.get_serializer(page, many=True)
        #     return self.get_paginated_response(serializer.data)
            
        # except (ValueError, TypeError):
        #     return Response(
        #         {'error': 'Invalid parameters provided'},
        #         status=status.HTTP_400_BAD_REQUEST
        #     )
   



class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = SkillFilterSet
    search_fields = ['name', 'description']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [AdminPermission()]

    @extend_schema(
        summary="List all skills",
        description="Get a list of all skills with optional filtering",
        parameters=[
            OpenApiParameter(
                name="category",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by skill category",
                enum=[choice[0] for choice in Skill.CATEGORY_CHOICES]
            ),
            OpenApiParameter(
                name="name",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Filter by skill name (case-insensitive partial match)"
            ),
            OpenApiParameter(
                name="has_volunteers",
                type=bool,
                location=OpenApiParameter.QUERY,
                description="Filter skills that have volunteers assigned"
            ),
            OpenApiParameter(
                name="min_proficiency",
                type=int,
                location=OpenApiParameter.QUERY,
                description="Filter skills by minimum average proficiency level"
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new skill",
        description="Create a new skill (Admin only)",
        request=SkillSerializer,
        responses={201: SkillSerializer},
        examples=[
            OpenApiExample(
                "Valid Skill Creation",
                value={
                    "name": "First Aid",
                    "category": "HEALTH",
                    "description": "Basic first aid and emergency response"
                },
                status_codes=["201"]
            )
        ]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Get skill statistics",
        description="Get statistics about skill usage and proficiency levels",
        responses={
            200: inline_serializer(
                name='SkillStats',
                fields={
                    'total_volunteers': serializers.IntegerField(),
                    'avg_proficiency': serializers.FloatField(),
                    'verified_count': serializers.IntegerField(),
                    'category_distribution': serializers.DictField()
                }
            )
        }
    )
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        skill = self.get_object()
        stats = {
            'total_volunteers': VolunteerSkill.objects.filter(skill=skill).count(),
            'avg_proficiency': VolunteerSkill.objects.filter(skill=skill).aggregate(
                Avg('proficiency_level')
            )['proficiency_level__avg'] or 0,
            'verified_count': VolunteerSkill.objects.filter(
                skill=skill, verified=True
            ).count(),
            'category_distribution': Skill.objects.filter(
                category=skill.category
            ).count()
        }
        return Response(stats)





class VolunteerSkillViewSet(viewsets.ModelViewSet):
    queryset = VolunteerSkill.objects.all()
    serializer_class = VolunteerSkillSerializer
    permission_classes = [IsAuthenticated, VolunteerPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_class = VolunteerSkillFilterSet

    def get_queryset(self):
        if self.request.user.has_role('ADMIN'):
            return self.queryset
        return self.queryset.filter(volunteer__user=self.request.user)


    @extend_schema(
        summary="Verify a volunteer skill",
        description="Mark a volunteer skill as verified (Admin only)",
        request=None,
        responses={
            200: inline_serializer(
                name='VerifyResponse',
                fields={
                    'status': serializers.CharField(),
                    'skill': VolunteerSkillSerializer()
                }
            ),
            403: OpenApiTypes.OBJECT
        }
    )
    @action(detail=True, methods=['post'])
    def verify_skill(self, request, pk=None):
        if not request.user.has_role('ADMIN'):
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        skill = self.get_object()
        skill.verified = True
        skill.verified_by = request.user
        skill.save()
        
        return Response({
            'status': 'skill verified',
            'skill': VolunteerSkillSerializer(skill).data
        })
    
    @extend_schema(
        summary="Bulk verify skills",
        description="Verify multiple volunteer skills at once (Admin only)",
        request=inline_serializer(
            name='BulkVerifyRequest',
            fields={
                'skill_ids': serializers.ListField(child=serializers.IntegerField())
            }
        ),
        responses={
            200: inline_serializer(
                name='BulkVerifyResponse',
                fields={
                    'verified_count': serializers.IntegerField(),
                    'skills': VolunteerSkillSerializer(many=True)
                }
            )
        }
    )
    @action(detail=False, methods=['post'])
    def bulk_verify(self, request):
        if not request.user.has_role('ADMIN'):
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )

        skill_ids = request.data.get('skill_ids', [])
        skills = VolunteerSkill.objects.filter(id__in=skill_ids)
        
        updated_count = skills.update(
            verified=True,
            verified_by=request.user
        )
        
        return Response({
            'verified_count': updated_count,
            'skills': VolunteerSkillSerializer(skills, many=True).data
        })
    
    @extend_schema(
        summary="Get volunteer skill progress",
        description="Get detailed progress information for a volunteer skill",
        responses={
            200: inline_serializer(
                name='SkillProgress',
                fields={
                    'skill_name': serializers.CharField(),
                    'proficiency_level': serializers.IntegerField(),
                    'verified': serializers.BooleanField(),
                    'time_since_verification': serializers.CharField(),
                    'similar_skills': SkillSerializer(many=True),
                    'next_level_requirements': serializers.CharField()
                }
            )
        }
    )
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        volunteer_skill = self.get_object()
        similar_skills = Skill.objects.filter(
            category=volunteer_skill.skill.category
        ).exclude(id=volunteer_skill.skill.id)[:3]
        
        response_data = {
            'skill_name': volunteer_skill.skill.name,
            'proficiency_level': volunteer_skill.proficiency_level,
            'verified': volunteer_skill.verified,
            'time_since_verification': (
                timezone.now() - volunteer_skill.updated_at
            ).days if volunteer_skill.verified else None,
            'similar_skills': SkillSerializer(similar_skills, many=True).data,
            'next_level_requirements': f"Requirements for level {min(volunteer_skill.proficiency_level + 1, 5)}"
        }
        return Response(response_data)
