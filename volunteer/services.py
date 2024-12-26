# from django.contrib.gis.geos import Point
# from django.contrib.gis.measure import D
# from django.contrib.gis.db.models.functions import Distance
# from typing import List
# from .models import Volunteer
# from django.db.models import Avg, Count, QuerySet





# class VolunteerLocationService:
#     @staticmethod
#     def find_nearby_volunteers(
#         point: Point,
#         max_distance: float,
#         specialties: List[str] = None,
#         experience_level: str = None,
#         is_available: bool = True
#     ) -> QuerySet:
#         """
#         Find nearby volunteers based on various criteria
        
#         Args:
#             point: Point object representing the center location
#             max_distance: Maximum distance in kilometers
#             specialties: Optional list of required skill categories
#             experience_level: Optional minimum experience level
#             is_available: Filter by availability status
            
#         Returns:
#             QuerySet of Volunteer objects ordered by distance
#         """
#         # Start with base queryset
#         queryset = Volunteer.objects.filter(is_available=is_available)
        
#         # Filter by location within max_distance
#         queryset = queryset.filter(
#             preferred_location__distance_lte=(point, D(km=max_distance))
#         ).annotate(
#             distance=Distance('preferred_location', point)
#         )
        
#         # Filter by experience level if specified
#         if experience_level:
#             experience_levels = {
#                 'BEGINNER': 0,
#                 'INTERMEDIATE': 1,
#                 'ADVANCED': 2,
#                 'EXPERT': 3
#             }
#             min_level = experience_levels.get(experience_level.upper(), 0)
#             queryset = queryset.filter(
#                 experience_level__in=[
#                     level for level, value in experience_levels.items()
#                     if value >= min_level
#                 ]
#             )
        
#         # Filter by specialties if specified
#         if specialties:
#             queryset = queryset.filter(
#                 skills__skill__category__in=specialties
#             ).distinct()
        
#         # Annotate with relevant metrics
#         queryset = queryset.annotate(
#             rating_count=Count('volunteerrating'),
#             avg_rating=Avg('volunteerrating__rating')
#         )
        
#         # Order by distance and then rating
#         return queryset.order_by('distance', '-avg_rating')