from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ResourceTagViewSet, ResourceDonationViewSet, ResourceViewSet, ResourceTypeViewSet
app_name = 'cddp-resource'

router = DefaultRouter()
router.register('cddp-resource-donation/', ResourceDonationViewSet)
router.register('cddp-resource-tag/', ResourceTagViewSet)
router.register('cddp-resourcce-type/', ResourceTypeViewSet)
router.register('cddp-resource/', ResourceViewSet )



urlpatterns = [
    path('', include(router.urls))
]