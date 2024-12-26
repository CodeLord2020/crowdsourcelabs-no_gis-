from django.shortcuts import render
from .serializers import *
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import viewsets, status
from .models import Resources, BlogResource, ProfilePicResource, IncidentMediaResource, CSRResourceMedia, EventResources
import cloudinary
from cloudinary.exceptions import Error as CloudinaryError
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
# Create your views here.


class ResourcesViewSets(viewsets.ModelViewSet):
    http_method_names = ["get", "patch", "post", "put", "delete"]
    serializer_class = CreateResourcesSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    queryset = Resources.objects.all()

    def get_serializer_class(self):
        if self.action in ['update', 'create', 'partial_update']:
            return CreateResourcesSerializer
        return ResourcesSerializer
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Attempt to delete the resource from Cloudinary
        if instance.cloud_id:
            try:
                cloudinary.uploader.destroy(public_id=instance.cloud_id, resource_type='raw')
                # print(f"Successfully deleted resource {instance.cloud_id} from Cloudinary")
            except Exception as e:
                pass
                # print(f"Error deleting resource from Cloudinary: {e}")
                # Optionally handle this error (e.g., log it, return a response, etc.)
        
        # Delete the instance from the database
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    


class BlogResourceViewSets(viewsets.ModelViewSet):
    http_method_names = ["get", "patch", "post", "put", "delete"]
    serializer_class = CreateBlogResourceSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    queryset = BlogResource.objects.all()

    def get_serializer_class(self):
        if self.action in ['update', 'create', 'partial_update']:
            return CreateBlogResourceSerializer
        return BlogResourceSerializer
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Attempt to delete the resource from Cloudinary
        if instance.cloud_id:
            try:
                cloudinary.uploader.destroy(public_id=instance.cloud_id, resource_type='raw')
                # print(f"Successfully deleted resource {instance.cloud_id} from Cloudinary")
            except Exception as e:
                pass
                # print(f"Error deleting resource from Cloudinary: {e}")
                # Optionally handle this error (e.g., log it, return a response, etc.)
        
        # Delete the instance from the database
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProfilePicResourceViewSets(viewsets.ModelViewSet):
    http_method_names = ["get", "patch", "post", "put", "delete"]
    serializer_class = CreateProfilePicResourceSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    queryset = ProfilePicResource.objects.all()

    def get_serializer_class(self):
        if self.action in ['update', 'create', 'partial_update']:
            return CreateProfilePicResourceSerializer
        return ProfilePicResourceSerializer
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Attempt to delete the resource from Cloudinary
        if instance.cloud_id:
            try:
                cloudinary.uploader.destroy(public_id=instance.cloud_id, resource_type='raw')
                # print(f"Successfully deleted resource {instance.cloud_id} from Cloudinary")
            except Exception as e:
                pass
                # print(f"Error deleting resource from Cloudinary: {e}")
                # Optionally handle this error (e.g., log it, return a response, etc.)
        
        # Delete the instance from the database
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    



class EventResourceViewSets(viewsets.ModelViewSet):
    http_method_names = ["get", "patch", "post", "put", "delete"]
    serializer_class = CreateEventResourcesSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    queryset = EventResources.objects.all()

    def get_serializer_class(self):
        if self.action in ['update', 'create', 'partial_update']:
            return CreateEventResourcesSerializer
        return EventResourcesSerializer
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Attempt to delete the resource from Cloudinary
        if instance.cloud_id:
            try:
                cloudinary.uploader.destroy(public_id=instance.cloud_id, resource_type='raw')
                # print(f"Successfully deleted resource {instance.cloud_id} from Cloudinary")
            except Exception as e:
                pass
                # print(f"Error deleting resource from Cloudinary: {e}")
                # Optionally handle this error (e.g., log it, return a response, etc.)
        
        # Delete the instance from the database
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class CSRResourceMediaViewSets(viewsets.ModelViewSet):
    http_method_names = ["get", "patch", "post", "put", "delete"]
    serializer_class = CreateCSRResourceMediaSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    queryset = CSRResourceMedia.objects.all()

    def get_serializer_class(self):
        if self.action in ['update', 'create', 'partial_update']:
            return CreateCSRResourceMediaSerializer
        return CSRResourceMediaSerializer
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Attempt to delete the resource from Cloudinary
        if instance.cloud_id:
            try:
                cloudinary.uploader.destroy(public_id=instance.cloud_id, resource_type='raw')
                # print(f"Successfully deleted resource {instance.cloud_id} from Cloudinary")
            except Exception as e:
                pass
                # print(f"Error deleting resource from Cloudinary: {e}")
                # Optionally handle this error (e.g., log it, return a response, etc.)
        
        # Delete the instance from the database
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
    



class IncidentMediaResourceViewSets(viewsets.ModelViewSet):
    http_method_names = ["get", "patch", "post", "put", "delete"]
    serializer_class = CreateIncidentMediaResourceSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    queryset = IncidentMediaResource.objects.all()

    def get_serializer_class(self):
        if self.action in ['update', 'create', 'partial_update']:
            return CreateIncidentMediaResourceSerializer
        return IncidentMediaResourceSerializer
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Attempt to delete the resource from Cloudinary
        if instance.cloud_id:
            try:
                cloudinary.uploader.destroy(public_id=instance.cloud_id, resource_type='raw')
                # print(f"Successfully deleted resource {instance.cloud_id} from Cloudinary")
            except Exception as e:
                pass
                # print(f"Error deleting resource from Cloudinary: {e}")
                # Optionally handle this error (e.g., log it, return a response, etc.)
        
        # Delete the instance from the database
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)