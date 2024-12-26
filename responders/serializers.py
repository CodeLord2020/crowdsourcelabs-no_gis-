from rest_framework import serializers
from accounts.serializers import UserSerializer
from .models import Specialization, Responder
from django.utils import timezone




class SpecializationSerializer(serializers.ModelSerializer):
    responder_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Specialization
        fields = ['id', 'name', 'description', 'required_certification',
                 'responder_count']
        read_only_fields = ['created_at', 'updated_at']
        

class ResponderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    specializations = SpecializationSerializer(many=True, read_only=True)
    days_until_certification_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = Responder
        fields = ['id', 'user', 'organization', 'certification_number',
                 'certification_expiry', 'specializations', 'is_on_duty',
                 'last_deployment', 'is_certified', 'days_until_certification_expiry']
        read_only_fields = ['created_at', 'updated_at','is_certified', 'last_deployment']

    def get_days_until_certification_expiry(self, obj):
        if obj.certification_expiry:
            delta = obj.certification_expiry - timezone.now().date()
            return delta.days
        return None

    def validate_certification_expiry(self, value):
        if value <= timezone.now().date():
            raise serializers.ValidationError(
                "Certification expiry date must be in the future"
            )
        return value
