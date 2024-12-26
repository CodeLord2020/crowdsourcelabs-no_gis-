from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from cloud_resource.models import BlogResource
# Create your models here.

User = get_user_model()


class BlogCategory(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name



class Blog(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='userblog')
    content = models.TextField()
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    resource = models.ForeignKey(BlogResource, on_delete=models.SET_NULL, null=True, blank=True )

    def __str__(self):
        return self.title
    
    def delete(self, *args, **kwargs):
        if self.resource:
            self.resource.delete()
        super().delete(*args, **kwargs)
    

    

class BlogComment(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='comments')
    author = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)
    content = models.TextField()

    def __str__(self):
        return f"Comment by {self.author} on {self.blog.title}"
