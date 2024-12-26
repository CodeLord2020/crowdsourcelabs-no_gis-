from django.db import models
from django.core.validators import MinLengthValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from typing import List
# from django.contrib.gis.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
# Create your models here.
User = get_user_model()


class Skill(models.Model):
    """Skills that volunteers can possess"""
    
    CATEGORY_CHOICES = [
        ('HEALTH', 'Health & Safety'),
        ('MANAGEMENT', 'Management & Leadership'),
        ('COMMUNICATION', 'Communication & Public Relations'),
        ('EDUCATION', 'Education & Tutoring'),
        ('TECH', 'Technology & IT Support'),
        ('LOGISTICS', 'Logistics & Transportation'),
        ('LANGUAGE', 'Language Skills'),
        ('ENVIRONMENT', 'Environmental Conservation'),
        ('ANIMAL_CARE', 'Animal Care'),
        ('MENTORING', 'Mentoring & Coaching'),
        ('ADMIN_SUPPORT', 'Administrative Support'),
        ('ARTS', 'Arts & Culture'),
        ('HUMAN_SERVICES', 'Human Services'),
        ('LEGAL', 'Legal Assistance'),
        ('FUNDRAISING', 'Fundraising & Grant Writing'),
        ('RESEARCH', 'Research & Data Analysis'),
        ('DISASTER_RELIEF', 'Disaster Relief'),
        ('ADVOCACY', 'Advocacy & Policy'),
        ('SPORTS', 'Sports & Recreation'),
        ('HOSPITALITY', 'Hospitality & Events'),
        ('OTHERS', 'Other Categories'),
    ]

    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, null=False, default="OTHERS")
    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('name', 'category')

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"
    

    
class Volunteer(models.Model):
    """Extended profile for volunteers"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    skills = models.ManyToManyField(Skill, through='VolunteerSkill')
    availability = models.JSONField(default=dict)
    experience_level = models.CharField(
        max_length=20,
        choices=[
            ('BEGINNER', 'Beginner'),
            ('INTERMEDIATE', 'Intermediate'),
            ('ADVANCED', 'Advanced'),
            ('EXPERT', 'Expert')
        ]
    )
    # preferred_location = models.PointField(null=True)
    max_travel_distance = models.IntegerField(default=10)  # in kilometers
    verified_hours = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    is_available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_rating(self):
        ratings = self.volunteerrating_set.all()
        if ratings:
            self.rating = sum([r.rating for r in ratings]) / len(ratings)
            self.save()

    def __str__(self):
        return f"{self.user.full_name} (Experience Level: {self.experience_level})"








class VolunteerSkill(models.Model):
    """Intermediary model for volunteer-skill relationship"""
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    proficiency_level = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='skill_verifications'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)




class VolunteerRating(models.Model):
    """Ratings given to volunteers"""
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE)
    rated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)