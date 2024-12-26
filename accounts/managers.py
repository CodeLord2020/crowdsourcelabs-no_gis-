from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    """Custom user manager with email as the unique identifier"""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):  #try to inject superadmi userrole object, issue with imports/dependencies
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)