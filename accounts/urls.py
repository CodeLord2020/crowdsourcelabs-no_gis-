from django.urls import path, include
from . import views 
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from rest_framework.routers import DefaultRouter
from .views import UserLocationViewSet, UserViewSet, UserRoleViewSet, RoleViewSet, VerifyUserView


router = DefaultRouter()
router.register(r'user-role', UserViewSet, basename='user_role'),
router.register(r'user_location', UserLocationViewSet, basename='user_location'),
router.register(r'role', UserViewSet, basename='role'),
router.register(r'auth', UserViewSet, basename='user'),



urlpatterns = [
    path('', include(router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('login',views.LoginView.as_view(), name='login' ),
    path('change-password',views.ChangePasswordView.as_view(), name='change-password' ),
    path('verify/<str:uid>/<str:token>/', views.verify_email, name='verify_email'),
    path('auth/verify/<str:uid>/<str:token>/', VerifyUserView.as_view(), name='verify-user'),
    path('password-reset/', views.PasswordResetRequestView.as_view(), name='password-reset'),
    path('resend-verification/', views.ResendVerificationLinkView.as_view(), name='resend-verification'),
    path('password-reset-confirm/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),  
]
