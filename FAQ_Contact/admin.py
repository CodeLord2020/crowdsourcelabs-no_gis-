from django.contrib import admin

# Register your models here.
from .models import FAQ, ContactRequest

admin.site.register(FAQ),
admin.site.register(ContactRequest)
