from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status, filters, generics, mixins, views
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import login, authenticate, logout
from rest_framework.permissions import IsAuthenticated,IsAuthenticatedOrReadOnly, AllowAny, BasePermission
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.db.models import Avg, Count, Q
from .filters import UserRoleFilter, RoleFilter, UserFilter
from .services import LocationService
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.gis.db.models.functions import Distance
from rest_framework.exceptions import APIException
from .utils import send_verification_email, send_password_reset_email
from rest_framework.request import Request
from django.contrib.auth.tokens import default_token_generator
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils.encoding import force_str
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from drf_spectacular.types import OpenApiTypes
from .permissions import (
    AdminPermission, 
)
from .models import (

    UserLocation,
    Role,
    UserRole
)
from .serializers import (
    UserRoleSerializer,
    UserSerializer,
    RoleSerializer,
    UserLocationSerializer,
    UserLocationSimpleSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    LoginSerializer,
    ChangePasswordSerializer,
)

from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
import logging
logger = logging.getLogger(__name__)
from django.contrib.auth import get_user_model
User = get_user_model()



# class IsOwnerOrStaff(BasePermission):
#     """Custom permission to only allow owners of an object to edit it"""
    
#     def has_object_permission(self, request, view, obj):
#         if request.user.is_staff:
#             return True
            

#         return obj.user == request.user
    

            
class UserLocationViewSet(viewsets.ModelViewSet):
    """
    Advanced ViewSet for managing user locations.
    
    Supports:
    - CRUD operations
    - Filtering by date range and accuracy
    - Custom actions for specific location updates
    - Bulk operations
    - Advanced querying capabilities
    """
    serializer_class = UserLocationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['location_accuracy', 'location_updated_at']
    search_fields = ['address']
    ordering_fields = ['location_updated_at', 'location_accuracy']
    ordering = ['-location_updated_at']

    def get_queryset(self):
        """
        Custom queryset that:
        1. Filters by user if specified
        2. Allows admin to see all locations
        3. Supports date range filtering
        """
        queryset = UserLocation.objects.all()

        # Regular users can only see their own location
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        # Date range filtering
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        
        if start_date:
            queryset = queryset.filter(location_updated_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(location_updated_at__lte=end_date)

        return queryset

    def perform_create(self, serializer):
        """Automatically associate the location with the current user"""
        serializer.save()
        logger.info(f"Location created for user {self.request.user}")

    def perform_update(self, serializer):
        """Handle updates with additional logging and validation"""
        old_location = self.get_object()
        instance = serializer.save()
        
        if old_location.coordinates != instance.coordinates:
            logger.info(
                f"Location updated for user {self.request.user}. "
                f"Old: {old_location.coordinates}, New: {instance.coordinates}"
            )

    @action(detail=True, methods=['post'])
    def quick_update(self, request, pk=None):
        """
        Quickly update location with minimal data
        POST /api/locations/{pk}/quick_update/
        """
        location = self.get_object()
        
        try:
            latitude = float(request.data.get('lat'))
            longitude = float(request.data.get('lng'))
            
            success = location.update_location(
                latitude=latitude,
                longitude=longitude,
                accuracy=request.data.get('accuracy')
            )
            
            if success:
                return Response(self.get_serializer(location).data)
            return Response(
                {"error": "Failed to update location"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except (ValueError, TypeError) as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    # @action(detail=False, methods=['get'])
    # def statistics(self, request):
    #     """
    #     Get location statistics for the user
    #     GET /api/locations/statistics/
    #     """
    #     queryset = self.get_queryset()
        
    #     stats = {
    #         'total_locations': queryset.count(),
    #         'average_accuracy': queryset.exclude(
    #             location_accuracy__isnull=True
    #         ).aggregate(models.Avg('location_accuracy'))['location_accuracy__avg'],
    #         'last_updated': queryset.first().location_updated_at if queryset.exists() else None,
    #         'has_current_location': queryset.filter(
    #             location_updated_at__gte=timezone.now() - timezone.timedelta(hours=1)
    #         ).exists()
    #     }
        
    #     return Response(stats)

    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """
        Bulk update multiple location records
        POST /api/locations/bulk_update/
        """
        locations = request.data.get('locations', [])
        updated = []
        errors = []

        for loc_data in locations:
            try:
                location = UserLocation.objects.get(id=loc_data.get('id'))
                serializer = self.get_serializer(
                    location,
                    data=loc_data,
                    partial=True
                )
                
                if serializer.is_valid():
                    serializer.save()
                    updated.append(serializer.data)
                else:
                    errors.append({
                        'id': loc_data.get('id'),
                        'errors': serializer.errors
                    })
            except UserLocation.DoesNotExist:
                errors.append({
                    'id': loc_data.get('id'),
                    'errors': 'Location not found'
                })
            except Exception as e:
                errors.append({
                    'id': loc_data.get('id'),
                    'errors': str(e)
                })

        return Response({
            'updated': updated,
            'errors': errors
        })
    


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='email',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by exact email match'
        ),
        OpenApiParameter(
            name='first_name',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by first name (case-insensitive contains)'
        ),
        OpenApiParameter(
            name='last_name',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter by last name (case-insensitive contains)'
        ),
        OpenApiParameter(
            name='min_age',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Filter users by minimum age'
        ),
        OpenApiParameter(
            name='max_age',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='Filter users by maximum age'
        ),
        OpenApiParameter(
            name='is_online',
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            description='Filter by online status (active in last 5 minutes)'
        ),
        OpenApiParameter(
            name='has_role',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter users by specific role'
        ),
        OpenApiParameter(
            name='has_any_role',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter users having any of the specified roles (comma-separated)'
        ),
        OpenApiParameter(
            name='has_all_roles',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='Filter users having all specified roles (comma-separated)'
        ),
        OpenApiParameter(
            name='is_profile_complete',
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            description='Filter by profile completion status'
        ),
    ]
)
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_class = UserFilter
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering_fields = ['date_joined', 'last_active', 'first_name', 'last_name']
    ordering = ['-date_joined']

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.has_role('ADMIN'):
            queryset = queryset.filter(id=self.request.user.id)
        return queryset


    def get_permissions(self):
        if self.action in ['create']:
            return []
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [AdminPermission()]
    
    @transaction.atomic
    def perform_create(self, serializer):
        user = serializer.save()
        token = default_token_generator.make_token(user)
          
        try:
            send_verification_email(user.email, token)
        except Exception as e:
                # If an error occurs during email sending, rollback the transaction
            user.delete()
            message = "There was an error with sending the registration email. Please try registering again."
            raise APIException(detail=message, code=status.HTTP_400_BAD_REQUEST)


    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


    @action(detail=True, methods=['post'])
    def assign_role(self, request, pk=None):
        if not request.user.has_role('ADMIN') and not request.user.has_role('SUPERADMIN'):
            return Response(
                {'detail': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        user = self.get_object()
        role_serializer = UserRoleSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if role_serializer.is_valid():
            role_serializer.save(user=user, assigned_by=request.user)
            return Response(role_serializer.data)
        return Response(
            role_serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    

    @action(detail=True, methods=['post'])
    def update_location(self, request, pk=None):
        user = self.get_object()
        location_serializer = UserLocationSerializer(data=request.data)
        if location_serializer.is_valid():
            location, _ = UserLocation.objects.get_or_create(user=user)
            for attr, value in location_serializer.validated_data.items():
                setattr(location, attr, value)
            location.save()
            return Response(UserLocationSerializer(location).data)
        return Response(
            location_serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        if not request.user.has_role('ADMIN') and not request.user.has_role('SUPERADMIN'):
            return Response(
                {'detail': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'detail': 'User deactivated successfully'})




class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    filterset_class = RoleFilter
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['role_type', 'description']
    ordering_fields = ['created_at', 'role_type']
    ordering = ['role_type']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [AdminPermission()]

    @extend_schema(
        summary="List all roles",
        parameters=[
            OpenApiParameter(
                name='created_after',
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                description='Filter roles created after specific datetime'
            ),
            OpenApiParameter(
                name='created_before',
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                description='Filter roles created before specific datetime'
            ),
            OpenApiParameter(
                name='has_users',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter roles that have assigned users'
            ),
            OpenApiParameter(
                name='role_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by role type'
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Get role usage statistics",
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['GET'])
    def statistics(self, request):
        stats = Role.objects.annotate(
            total_users=Count('userrole__user', distinct=True),
            active_users=Count(
                'userrole__user',
                distinct=True,
                filter=Q(userrole__is_active=True)
            )
        ).values('role_type', 'total_users', 'active_users')
        
        return Response(stats)






class UserRoleViewSet(viewsets.ModelViewSet):
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    filterset_class = UserRoleFilter
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__username', 'user__email', 'role__role_type']
    ordering_fields = ['assigned_at', 'is_active']
    ordering = ['-assigned_at']

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'get_my_roles']:
            return [IsAuthenticated()]
        return [AdminPermission()]

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)

    @extend_schema(
        summary="List all user roles",
        parameters=[
            OpenApiParameter(
                name='assigned_after',
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                description='Filter roles assigned after specific datetime'
            ),
            OpenApiParameter(
                name='assigned_before',
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                description='Filter roles assigned before specific datetime'
            ),
            OpenApiParameter(
                name='assigned_by_username',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by username of the assigner'
            ),
            OpenApiParameter(
                name='role_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by role type',
                enum=[choice[0] for choice in Role.ROLE_CHOICES]
            ),
            OpenApiParameter(
                name='is_active',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by active status'
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Get current user's roles",
        responses={200: UserRoleSerializer(many=True)}
    )
    @action(detail=False, methods=['GET'])
    def my_roles(self, request):
        queryset = self.get_queryset().filter(
            user=request.user,
            is_active=True
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Bulk assign roles to users",
        request=OpenApiTypes.OBJECT,
        responses={201: UserRoleSerializer(many=True)}
    )
    @action(detail=False, methods=['POST'])
    def bulk_assign(self, request):
        """
        Bulk assign roles to users
        Request format:
        {
            "assignments": [
                {"user_id": 1, "role_id": 1},
                {"user_id": 2, "role_id": 1}
            ]
        }
        """
        assignments = request.data.get('assignments', [])
        created_roles = []

        for assignment in assignments:
            serializer = self.get_serializer(data=assignment)
            if serializer.is_valid():
                user_role = serializer.save(assigned_by=request.user)
                created_roles.append(user_role)
            else:
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

        response_serializer = self.get_serializer(created_roles, many=True)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )

    @extend_schema(
        summary="Deactivate user role",
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=True, methods=['POST'])
    def deactivate(self, request, pk=None):
        user_role = self.get_object()
        if not user_role.is_active:
            return Response(
                {'message': 'Role is already inactive'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_role.is_active = False
        user_role.save()
        return Response({'message': 'Role deactivated successfully'})

    @extend_schema(
        summary="Get role assignment history",
        responses={200: OpenApiTypes.OBJECT}
    )
    @action(detail=False, methods=['GET'])
    def assignment_history(self, request):
        user_id = request.query_params.get('user_id')
        role_id = request.query_params.get('role_id')
        
        queryset = self.get_queryset()
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if role_id:
            queryset = queryset.filter(role_id=role_id)
            
        queryset = queryset.order_by('user', '-assigned_at')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    




class ResendVerificationLinkView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetRequestSerializer

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Verification email sent successfully"),
            400: OpenApiResponse(description="Invalid email or user already verified"),
            404: OpenApiResponse(description="User not found"),
        },
        description="Resend verification email to unverified users"
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']


            # try:
            #     validate_email(email)
            # except ValidationError:
            #     return Response({"error": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            if user.is_verified:
                return Response({"error": "User is already verified"}, status=status.HTTP_400_BAD_REQUEST)

            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            try:
                send_verification_email(email, token)
            except Exception as e:
                return Response({"error": "Failed to send verification email"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({"message": "Verification email sent successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


class ChangePasswordView(generics.GenericAPIView, mixins.UpdateModelMixin):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer  # You need to define this serializer

    # def post(self, request, *args, **kwargs):
    #     return self.update(request, *args, **kwargs)

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            old_password = serializer.validated_data.get('old_password')
            new_password = serializer.validated_data.get('new_password')
            confirm_password = serializer.validated_data.get('confirm_password')

            # Ensure the old password is correct
            if not self.object.check_password(old_password):
                return Response({'error': 'Old password is incorrect.'}, status=status.HTTP_400_BAD_REQUEST)

            # Ensure new password and confirm password match
            if new_password != confirm_password:
                return Response({'error': 'New password and confirm password do not match.'}, status=status.HTTP_400_BAD_REQUEST)

            # Set the new password
            self.object.set_password(new_password)
            self.object.save()
            return Response({'message': 'Password changed successfully.'}, status=status.HTTP_202_ACCEPTED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyUserView(views.APIView):
    """View to verify user via email token"""
    permission_classes = [AllowAny]

    def get(self, request, uid, token):
        try:
            # Decode the UID and fetch the user
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"detail": "Invalid UID or User does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the token is valid
        if default_token_generator.check_token(user, token):
            # Mark the user as verified
            user.is_active = True  
            user.is_verified = True
            user.save()

            return Response({"detail": "User successfully verified."}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)


def verify_email(request, uid, token):
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_verified = True
        user.save()
        return render(request, 'verify-success.html')
    else:
        return render(request, 'verify-fail.html')
    

class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = User.objects.get(email=email)
                send_password_reset_email(user)
                return Response({"detail": "Password reset email sent."}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"detail": "User with this email does not exist."}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
     


class PasswordResetConfirmView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = PasswordResetConfirmSerializer
    def post(self, request, *args, **kwargs):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Password has been reset successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LoginView(generics.CreateAPIView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"message": "Invalid email and password"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_verified:
            return Response(
                {"message": "Account is not verified. Please verify your account to login."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        
        user = authenticate(email=email, password=password)

        if user is not None:
            # roles = [role.role_type for role in user.userrole_set.all()]
            login(request, user)
            refresh = RefreshToken.for_user(user)
            return Response(
        {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "message": "login successful",
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "roles": user.get_roles()
            
        },
        status=status.HTTP_200_OK,
    )

        return Response(
            {"message": "Invalid email and password"},
            status=status.HTTP_401_UNAUTHORIZED,
        )
        

