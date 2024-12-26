from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FAQViewSet, ContactRequestViewSet

router = DefaultRouter()
router.register(r'faq', FAQViewSet)
router.register(r'contact', ContactRequestViewSet)

urlpatterns = [
    path('', include(router.urls)),
]