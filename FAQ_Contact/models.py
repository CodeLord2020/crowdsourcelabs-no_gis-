from django.db import models

# Create your models here.
from django.db.models import Q



class FAQManager(models.Manager):
    def search(self, query):
        return self.filter(
            Q(question__icontains=query) | Q(answer__icontains=query)
        )


class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = FAQManager()

    def __str__(self):
        return self.question
    


class ContactRequest(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.subject} - {self.name}"
    

