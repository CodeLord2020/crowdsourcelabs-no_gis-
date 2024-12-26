from rest_framework import serializers
from .models import Resources, ProfilePicResource, BlogResource, IncidentMediaResource, CSRResourceMedia, EventResources
import cloudinary.uploader
from rest_framework.validators import ValidationError



RESOURCE_TYPES = (
    ("AUDIO", "AUDIO"),
    ("VIDEO", "VIDEO"),
    ("IMAGE", "IMAGE"),
    ("DOCUMENT", "DOCUMENT"),
    ("OTHERS", "OTHERS"),
)



MAXIMUM_SIZE_UPLOAD = 3 * 1024 * 1024 #3mb


class BaseResourceSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True, write_only=True)
    title = serializers.CharField(required=True)
    type = serializers.ChoiceField(choices=(
        ("AUDIO", "AUDIO"),
        ("VIDEO", "VIDEO"),
        ("IMAGE", "IMAGE"),
        ("DOCUMENT", "DOCUMENT"),
        ("OTHERS", "OTHERS"),
    ), required=True)

    class Meta:
        fields = [
            "id",
            "title",
            "file",
            "type",
            "size",
            "media_url",
            "cloud_id",
        ]
        read_only_fields = ["id", "media_url", "cloud_id", "size"]

    def validate_file(self, value):
        if value.size > MAXIMUM_SIZE_UPLOAD:
            raise ValidationError("File size must not exceed 3MB")
        return value

    def upload_to_cloudinary(self, file):
        return cloudinary.uploader.upload(file, resource_type='raw')

    def create(self, validated_data):
        file = validated_data.pop('file')
        upload_result = self.upload_to_cloudinary(file)

        # Create a new instance with the uploaded data
        instance = self.Meta.model.objects.create(
            media_url=upload_result["url"],
            cloud_id=upload_result["public_id"],
            size=upload_result["bytes"],
            **validated_data,
        )
        return instance

    def update(self, instance, validated_data):
        file = validated_data.pop('file', None)
        if file:
            # Delete old Cloudinary resource
            cloudinary.uploader.destroy(public_id=instance.cloud_id, resource_type='raw')

            # Upload new file
            upload_result = self.upload_to_cloudinary(file)
            instance.media_url = upload_result["url"]
            instance.cloud_id = upload_result["public_id"]
            instance.size = upload_result["bytes"]

        # Update other fields
        instance.title = validated_data.get('title', instance.title)
        instance.type = validated_data.get('type', instance.type)
        instance.save()
        return instance



class CreateResourcesSerializer(BaseResourceSerializer):
    class Meta(BaseResourceSerializer.Meta):
        model = Resources

class ResourcesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resources
        fields = "__all__"


class CreateProfilePicResourceSerializer(BaseResourceSerializer):
    class Meta(BaseResourceSerializer.Meta):
        model = ProfilePicResource
    
class ProfilePicResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfilePicResource
        fields = "__all__"


class CreateBlogResourceSerializer(BaseResourceSerializer):
    class Meta(BaseResourceSerializer.Meta):
        model = BlogResource

class BlogResourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = BlogResource
        fields = "__all__"








class IncidentMediaResourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = IncidentMediaResource
        fields = "__all__"


class CreateIncidentMediaResourceSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True, write_only=True)
    title = serializers.CharField(required=True)
    type = serializers.ChoiceField(RESOURCE_TYPES, required=True)


    class Meta:
        model = IncidentMediaResource
        fields = [
            "id",
            "title",
            "file",
            "type",
            'is_sensitive',
            'caption',
            "size",
            "media_url",
            "cloud_id",
        ]
        read_only_fields = ["id", "media_url", "cloud_id", "size"]

    def validate_file(self, value):
        if value.size > MAXIMUM_SIZE_UPLOAD:
            raise ValidationError("File size must not be more than 2MB")
        return value

    def create(self, validated_data):
        file = validated_data.pop('file')  # Extract 'file' from validated_data

        # Upload the file to Cloudinary or your desired storage
        upload_result = cloudinary.uploader.upload(file, resource_type='raw')

        # Create a new Resources instance with the other fields
        instance = IncidentMediaResource.objects.create(
            media_url=upload_result["url"],
            cloud_id=upload_result["public_id"],
            size=upload_result["bytes"],
            **validated_data,
        )

        return instance

    def update(self, instance, validated_data):
        file = validated_data.pop('file', None)  # Extract 'file' from validated_data

        if file:
            # Delete the old file in Cloudinary
            cloudinary.uploader.destroy(public_id=instance.cloud_id, resource_type='raw')

            # Upload the new file to Cloudinary or your desired storage
            upload_result = cloudinary.uploader.upload(file, resource_type='raw')

            # Update the media_url and cloud_id with the new values
            instance.media_url = upload_result["url"]
            instance.cloud_id = upload_result["public_id"]
            instance.size = upload_result["bytes"]

        # Update other fields as needed
        instance.title = validated_data.get('title', instance.title)
        instance.type = validated_data.get('type', instance.type)
        instance.save()
        return instance




class EventResourcesSerializer(serializers.ModelSerializer):

    class Meta:
        model = EventResources
        fields = "__all__"


class CreateEventResourcesSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True, write_only=True)
    title = serializers.CharField(required=True)
    type = serializers.ChoiceField(RESOURCE_TYPES, required=True)


    class Meta:
        model = EventResources
        fields = [
            "id",
            "title",
            "file",
            "type",
            'is_sensitive',
            'caption',
            "size",
            "media_url",
            "cloud_id",
        ]
        read_only_fields = ["id", "media_url", "cloud_id", "size"]

    def validate_file(self, value):
        if value.size > MAXIMUM_SIZE_UPLOAD:
            raise ValidationError("File size must not be more than 2MB")
        return value

    def create(self, validated_data):
        file = validated_data.pop('file')  # Extract 'file' from validated_data

        # Upload the file to Cloudinary or your desired storage
        upload_result = cloudinary.uploader.upload(file, resource_type='raw')

        # Create a new Resources instance with the other fields
        instance = EventResources.objects.create(
            media_url=upload_result["url"],
            cloud_id=upload_result["public_id"],
            size=upload_result["bytes"],
            **validated_data,
        )

        return instance

    def update(self, instance, validated_data):
        file = validated_data.pop('file', None)  # Extract 'file' from validated_data

        if file:
            # Delete the old file in Cloudinary
            cloudinary.uploader.destroy(public_id=instance.cloud_id, resource_type='raw')

            # Upload the new file to Cloudinary or your desired storage
            upload_result = cloudinary.uploader.upload(file, resource_type='raw')

            # Update the media_url and cloud_id with the new values
            instance.media_url = upload_result["url"]
            instance.cloud_id = upload_result["public_id"]
            instance.size = upload_result["bytes"]

        # Update other fields as needed
        instance.title = validated_data.get('title', instance.title)
        instance.type = validated_data.get('type', instance.type)
        instance.save()
        return instance







class CreateCSRResourceMediaSerializer(BaseResourceSerializer):
    class Meta(BaseResourceSerializer.Meta):
        model = CSRResourceMedia
        

class CSRResourceMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CSRResourceMedia
        fields = "__all__"
