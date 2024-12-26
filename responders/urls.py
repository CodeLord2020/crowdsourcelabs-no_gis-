from django.urls import path, include
from . import views 

from rest_framework.routers import DefaultRouter
from .views import ResponderViewSet, SpecializationViewSet


router = DefaultRouter()
router.register(r'specialization', SpecializationViewSet, basename='specialization')
router.register(r'', ResponderViewSet, basename='responder')


urlpatterns = [
    path('', include(router.urls)),
]
