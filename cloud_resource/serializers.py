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


class ResourcesSerializer(serializers.ModelSerializer):

    class Meta:
        model = Resources
        fields = "__all__"


class CreateResourcesSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True, write_only=True)
    title = serializers.CharField(required=True)
    type = serializers.ChoiceField(RESOURCE_TYPES, required=True)


    class Meta:
        model = Resources
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
            raise ValidationError("File size must not be more than 2MB")
        return value

    def create(self, validated_data):
        file = validated_data.pop('file')  # Extract 'file' from validated_data

        # Upload the file to Cloudinary or your desired storage
        upload_result = cloudinary.uploader.upload(file, resource_type='raw')

        # Create a new Resources instance with the other fields
        instance = Resources.objects.create(
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
    
    
class BlogResourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = BlogResource
        fields = "__all__"


class CreateBlogResourceSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True, write_only=True)
    title = serializers.CharField(required=True)
    type = serializers.ChoiceField(RESOURCE_TYPES, required=True)


    class Meta:
        model = BlogResource
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
            raise ValidationError("File size must not be more than 2MB")
        return value

    def create(self, validated_data):
        file = validated_data.pop('file')  # Extract 'file' from validated_data

        # Upload the file to Cloudinary or your desired storage
        upload_result = cloudinary.uploader.upload(file, resource_type='raw')

        # Create a new Resources instance with the other fields
        instance = BlogResource.objects.create(
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
    
    
class ProfilePicResourceSerializer(serializers.ModelSerializer):

    class Meta:
        model = ProfilePicResource
        fields = "__all__"


class CreateProfilePicResourceSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True, write_only=True)
    title = serializers.CharField(required=True)
    type = serializers.ChoiceField(RESOURCE_TYPES, required=True)


    class Meta:
        model = ProfilePicResource
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
            raise ValidationError("File size must not be more than 2MB")
        return value

    def create(self, validated_data):
        file = validated_data.pop('file')  # Extract 'file' from validated_data

        # Upload the file to Cloudinary or your desired storage
        upload_result = cloudinary.uploader.upload(file, resource_type='raw')

        # Create a new Resources instance with the other fields
        instance = ProfilePicResource.objects.create(
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





class CSRResourceMediaSerializer(serializers.ModelSerializer):

    class Meta:
        model = CSRResourceMedia
        fields = "__all__"


class CreateCSRResourceMediaSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True, write_only=True)
    title = serializers.CharField(required=True)
    type = serializers.ChoiceField(RESOURCE_TYPES, required=True)


    class Meta:
        model = CSRResourceMedia
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
            raise ValidationError("File size must not be more than 2MB")
        return value

    def create(self, validated_data):
        file = validated_data.pop('file')  # Extract 'file' from validated_data

        # Upload the file to Cloudinary or your desired storage
        upload_result = cloudinary.uploader.upload(file, resource_type='raw')

        # Create a new Resources instance with the other fields
        instance = CSRResourceMedia.objects.create(
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