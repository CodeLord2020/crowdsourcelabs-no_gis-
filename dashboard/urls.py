from rest_framework.routers import DefaultRouter
from .views import DashboardViewSet

router = DefaultRouter()
router.register(r'incident-resorce', DashboardViewSet, basename='incident-resorce')

urlpatterns = [
    # Other URL patterns...
] + router.urls
