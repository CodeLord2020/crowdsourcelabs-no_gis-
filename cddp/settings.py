"""
Django settings for cddp project.

Generated by 'django-admin startproject' using Django 5.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

from pathlib import Path
import dj_database_url
from decouple import config
import os
import cloudinary
from datetime import timedelta
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY")


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = ['crowdsourcelab.onrender.com' , 'localhost' , '127.0.0.1']
AUTH_USER_MODEL = "accounts.User"
GEOIP_PATH = os.path.join(BASE_DIR, 'geoip')
FRONTEND_URL = config("FRONTEND_URL")

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    'django.contrib.gis',
    'leaflet',

    'accounts',
    'blog',
    'cddp',
    'cddpresources',
    'cloud_resource',
    'dashboard',
    'event',
    'FAQ_Contact',
    'incident',
    'reporters',
    'responders',
    'volunteer',

    # third-party-apps
    "rest_framework",
    'django_filters',
    "corsheaders",
    "django_celery_beat",
    "rest_framework.authtoken",
    'drf_spectacular',
    'cloudinary_storage',
    'cloudinary',
    'geoip2',
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# GDAL_LIBRARY_PATH = os.path.join("/usr/local/opt/gdal/lib/libgdal.dylib")
# GDAL_LIBRARY_PATH = os.getenv('GDAL_LIBRARY_PATH', r'C:\OSGeo4W\bin\gdal309.dll')

ROOT_URLCONF = "cddp.urls"
CORS_ALLOW_ALL_ORIGINS = True
CLIENT_URL = config('CLIENT_URL')

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ['templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "cddp.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": BASE_DIR / "db.sqlite3",
#     }
# }

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        # 'ENGINE': 'django.db.backends.postgresql',  # Django's built-in PostgreSQL backend
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
        'OPTIONS': {
            'sslmode': config('DB_SSLMODE', default='require'),
        },
    }
}

# Celery Configuration
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60

CELERY_IMPORTS = ("cddp.tasks")

# Django Celery Beat
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

REST_FRAMEWORK = {
    "NON_FIELD_ERRORS_KEY": "errors",
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated", ),
    "DEFAULT_PAGINATION_CLASS": "cddp.pagination.CustomPagination",
    "PAGE_SIZE": 10,

    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend',
                                'rest_framework.filters.OrderingFilter'],
}

SPECTACULAR_SETTINGS = {
    "SCHEMA_PATH_PREFIX": r"/api/v1",
    "DEFAULT_GENERATOR_CLASS": "drf_spectacular.generators.SchemaGenerator",
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "COMPONENT_SPLIT_PATCH": True,
    "COMPONENT_SPLIT_REQUEST": True,
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
    },
    "UPLOADED_FILES_USE_URL": True,
    "TITLE": "Crowdsourced",
    "DESCRIPTION": "Crowdsourced Response Platform APIs",
    "VERSION": "1.0.0",
    "LICENCE": {"name": "BSD License"},
    "CONTACT": {"name": "Rasheed Babatunde Zen ", "email": "brasheed240@gmail.com"},
}


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=12),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=2),
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    # "Bearer <Token>"
}
# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST")
EMAIL_PORT = config("EMAIL_PORT")
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
# EMAIL_USE_TLS = config("EMAIL_USE_TLS")
ADMIN_EMAIL =config("ADMIN_EMAIL")
EMAIL_USE_SSL = True


cloudinary.config(
    cloud_name=config('CLOUD_NAME'),
    api_key=config("API_KEY"),
    api_secret=config("API_SECRET"),
)


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{asctime} {levelname} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',  # Adjust to INFO for less verbosity
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'location_updates.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',  # Log errors and critical events
        },
        'location_logger': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',  # Logs at DEBUG level for development, can adjust in prod
            'propagate': False,
        },
    },
}
