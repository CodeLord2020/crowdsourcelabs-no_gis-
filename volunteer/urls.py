from django.urls import path, include
from . import views 

from rest_framework.routers import DefaultRouter
from .views import VolunteerViewSet, SkillViewSet, VolunteerSkillViewSet


router = DefaultRouter()
router.register(r'skill', SkillViewSet, basename='skill')
router.register(r'volunteer-skill', VolunteerSkillViewSet, basename='volunteer-skill')
router.register(r'', VolunteerViewSet, basename='volunteer')

urlpatterns = [
    path('', include(router.urls)),
]
