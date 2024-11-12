from rest_framework import serializers
from .models import FAQ, ContactRequest



class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = ['id', 'question', 'answer', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']



class ContactRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactRequest
        fields = ['id', 'name', 'email', 'subject', 'message', 'created_at', 'is_resolved']
        read_only_fields = ['id', 'created_at', 'is_resolved']

    def validate(self, data):
        # Check if the user is authenticated
        user = self.context['request'].user

        # If user is authenticated and email is not provided, set the user's email
        if user.is_authenticated:
            if not data.get('email'):
                data['email'] = user.email

        # If user is not authenticated, ensure email is provided
        elif not data.get('email'):
            raise serializers.ValidationError({'email': 'This field is required for unauthenticated users.'})

        return data

