from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResourcesViewSets, ProfilePicResourceViewSets, CSRResourceMediaViewSets, BlogResourceViewSets, IncidentMediaResourceViewSets

app_name = 'cloud_resource'

router = DefaultRouter()
router.register('', ResourcesViewSets)
router.register('profile-pics/', ProfilePicResourceViewSets)
router.register('incident-media/', IncidentMediaResourceViewSets)
router.register('csr-media-resource/', CSRResourceMediaViewSets )
router.register('blogs-media/', BlogResourceViewSets)



urlpatterns = [
    path('', include(router.urls))
]