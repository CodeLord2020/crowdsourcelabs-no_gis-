from rest_framework.routers import DefaultRouter
from .views import( ResourceManagementViewSet, IncidentCategoryViewSet,
                    TaskViewSet, IncidentViewSet)

router = DefaultRouter()
router.register(r'resources', ResourceManagementViewSet, basename='resource')
router.register(r'incident-category', IncidentCategoryViewSet, basename='incident-category')
router.register(r'incident', IncidentViewSet, basename='incident')
router.register(r'tasks', TaskViewSet, basename='tasks')



urlpatterns = [

] + router.urls
