"""
Local development settings for Local Food backend.
"""
import os
from pathlib import Path

# Set environment variables that base settings might need
os.environ.setdefault("SECRET_KEY", "django-insecure-local-development-key-change-in-production")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("ALLOWED_CLIENT_HOSTS", "localhost,127.0.0.1")

# Import all base settings using exec to avoid package issues
import sys
import os
settings_file = Path(__file__).resolve().parent.parent / "settings.py"
with open(settings_file, 'r') as f:
    settings_code = f.read()

# Execute the settings.py code in the current namespace
exec(settings_code, globals())

# Override BASE_DIR for local development
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Enable local development mode
LOCAL_DEVELOPMENT = True

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-local-development-key-change-in-production"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Database configuration for local development
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "localfood_dev.db",
    }
}

# Add local food app to existing INSTALLED_APPS
INSTALLED_APPS = INSTALLED_APPS + [
    "saleor.localfood",
]

# Add debug toolbar for development
if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Add debug toolbar middleware
if DEBUG:
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

ROOT_URLCONF = "saleor.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "saleor.wsgi.application"

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# GraphQL settings
GRAPHENE = {
    "SCHEMA": "saleor.graphql.schema.schema",
    "MIDDLEWARE": [],
}

# Mock external services
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Internal IPs for debug toolbar
INTERNAL_IPS = ["127.0.0.1", "localhost"]

# Celery configuration for local development
CELERY_TASK_ALWAYS_EAGER = True  # Execute tasks synchronously
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND = "redis://localhost:6379/0"

# Local Food specific settings
WAREHOUSE_NOTIFICATION_EMAILS = ["dev@localfood.com", "warehouse@localfood.com"]
DEFAULT_FROM_EMAIL = "noreply@localfood.com"

# Disable webhooks for local development
ENABLE_WEBHOOKS = False

# Authentication (simplified for development)
AUTH_USER_MODEL = "localfood.MockUser"

# Password validation (simplified for development)
AUTH_PASSWORD_VALIDATORS = []

# Cache (use dummy cache for development)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "saleor.localfood": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Development specific settings
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Security settings (relaxed for development)
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_HSTS_SECONDS = 0
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False