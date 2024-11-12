from django.db import models
from django.core.validators import MinLengthValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from typing import List
from django.contrib.gis.db import models

from django.contrib.auth import get_user_model
# Create your models here.

User = get_user_model()

class Reporter(models.Model):
    """Extended profile for incident reporters"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    credibility_score = models.FloatField(default=0.0)
    reports_submitted = models.IntegerField(default=0)
    reports_verified = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def verification_rate(self) -> float:
        return self.reports_verified / self.reports_submitted if self.reports_submitted > 0 else 0

    def update_credibility_score(self):
        self.credibility_score = (
            (self.verification_rate * 0.7) +
            (min(self.reports_submitted, 100) / 100 * 0.3)
        )
        self.save()

    