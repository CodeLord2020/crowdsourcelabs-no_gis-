from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
# Create your models here.

User = get_user_model()



class Specialization(models.Model):
    """Specializations for responders"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    required_certification = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name
    


class Responder(models.Model):
    """Extended profile for emergency responders"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='responder')
    organization = models.CharField(max_length=100)
    certification_number = models.CharField(max_length=50, unique=True, null= True, blank=True)
    certification_expiry = models.DateField()
    specializations = models.ManyToManyField(Specialization)
    is_on_duty = models.BooleanField(default=False)
    last_deployment = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def is_certified(self) -> bool:
        return self.certification_expiry > timezone.now().date()

    def validate_certification(self):
        if not self.is_certified:
            self.user.userrole_set.filter(role__role_type='RESPONDER').update(is_active=False)

    def __str__(self) -> str:
        return self.user.full_name
    



