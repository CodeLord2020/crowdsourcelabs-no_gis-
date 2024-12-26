from rest_framework import serializers
from accounts.serializers import UserSerializer
from .models import Reporter




class ReporterSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Reporter
        fields = ['id', 'user', 'credibility_score', 'reports_submitted',
                 'reports_verified', 'verification_rate']
        read_only_fields = ['created_at', 'updated_at','credibility_score', 'reports_submitted',
                           'reports_verified']