from django.urls import path, include
from . import views 

from rest_framework.routers import DefaultRouter
from .views import ReporterViewSet


router = DefaultRouter()
router.register(r'', ReporterViewSet, basename='reporter')
# router.register(r'', UserLocationViewSet, basename='userlocation')

urlpatterns = [
    path('', include(router.urls)),
]
