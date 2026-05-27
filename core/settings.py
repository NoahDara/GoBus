from pathlib import Path
import os
import platform
import loguru
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = "lqg(hu*=5fq)t*j&k+2&=43of5(a5k_h)eatn#r(g+_p4^y45!"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=False)

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'django.contrib.sites', 
    'allauth',
    'allauth.account',
    'allauth.socialaccount', 
    
    #Installed apps
    'accounts.apps.AccountsConfig',
    'bookings.apps.BookingsConfig',
    'buses.apps.BusesConfig',
    'dashboard.apps.DashboardConfig',
    'drivers.apps.DriversConfig',
    'notifications.apps.NotificationsConfig',
    'payments.apps.PaymentsConfig',
    
    #3rd party apps
    "debug_toolbar",
    "crispy_forms",
    "crispy_bootstrap5", 
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates/')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.request',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
MYSQL_DB_NAME = config("MYSQL_DB_NAME")
MYSQL_DB_USER = config("MYSQL_DB_USER")
MYSQL_DB_PASSWORD = config("MYSQL_DB_PASSWORD")
MYSQL_DB_HOST = config("MYSQL_DB_HOST")
MYSQL_DB_PORT = config("MYSQL_DB_PORT")
USE_MYSQL = config("USE_MYSQL", default=False, cast=bool)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql" if USE_MYSQL else "django.db.backends.sqlite3",
        "NAME": MYSQL_DB_NAME if USE_MYSQL else BASE_DIR / "db.sqlite3",
        "USER": MYSQL_DB_USER if USE_MYSQL else None,
        "PASSWORD": MYSQL_DB_PASSWORD if USE_MYSQL else None,
        "HOST": MYSQL_DB_HOST if USE_MYSQL else None,
        "PORT": MYSQL_DB_PORT if USE_MYSQL else None,
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = "/static/"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [BASE_DIR / "static"]

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
 
# ============================================================================
# AUTHENTICATION BACKENDS (if using django-allauth)
# ============================================================================
 
AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',
    
    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
]


LOGIN_REDIRECT_URL = 'dashboard'
ACCOUNT_LOGOUT_REDIRECT = "login"

# Emails
EMAIL_BACKEND = 'config.helpers.DynamicEmailBackend'

ADMINS = [
    ("noah", "noahdara2004@gmail.com"),]

path_separator = "\\" if platform.system() == "Windows" else "/"
ASN_FILE_DESTINATION = os.path.join(BASE_DIR, f"media{path_separator}asn{path_separator}")
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"
TEST_FILE_STORAGE = os.path.join(BASE_DIR, f"test-data{path_separator}results.xlsx")

STATUS_CHOICES = (('success', 'Success'), ('failed', 'Failed'),('pending', 'Pending'), ('rejected', 'Rejected'))

LOGGER = loguru.logger

DEBUG_TOOLBAR_ENABLED = config("DEBUG_TOOLBAR_ENABLED", default=False)
if DEBUG_TOOLBAR_ENABLED:
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: True  
    }
else:
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK": lambda request: False  
    }
    
CSRF_TRUSTED_ORIGINS = [
    'https://*.ngrok-free.app'
]  
    
if not DEBUG:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "file": {
                "level": "ERROR",
                "class": "logging.FileHandler",
                "filename": os.path.join(BASE_DIR, "debug.log"),
            },
        },
        "loggers": {
            "django": {
                "handlers": ["file"],
                "level": "ERROR",
                "propagate": True,
            },
        },
    }
else:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "{levelname} {name} {message}",
                "style": "{",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
            },
        },
        "loggers": {
            "": {  # root logger, catches all
                "handlers": ["console"],
                "level": "DEBUG",
            },
        },
    }
    
from helpers.task_manager import get_task_manager
TASK_MANAGER = get_task_manager()  

SITE_ID = 1

TIME_ZONE = 'Africa/Harare'


ASGI_APPLICATION = 'core.asgi.application'

PAYNOW_INTEGRATION_ID = 'your-id'
PAYNOW_INTEGRATION_KEY = 'your-key'
PAYNOW_DOMAIN = 'localhost:8000' if DEBUG else 'yourdomain.com'

# ============================================================================
# GOOGLE OAUTH CONFIGURATION
# ============================================================================
 
# Google OAuth 2.0 Credentials
# Get these from Google Cloud Console: https://console.cloud.google.com
GOOGLE_OAUTH_CLIENT_ID = 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com'
GOOGLE_OAUTH_CLIENT_SECRET = 'YOUR_GOOGLE_CLIENT_SECRET'
 
# Google OAuth Redirect URI (must match Google Console configuration)
# For local development:
# GOOGLE_OAUTH_REDIRECT_URI = 'http://localhost:8000/accounts/google/callback/'
# For production:
# GOOGLE_OAUTH_REDIRECT_URI = 'https://yourdomain.com/accounts/google/callback/'
 
GOOGLE_OAUTH_REDIRECT_URI = os.getenv(
    'GOOGLE_OAUTH_REDIRECT_URI',
    'http://localhost:8000/accounts/google/callback/'
)
 
 
# ============================================================================
# DJANGO-ALLAUTH SETTINGS (Optional - makes OAuth easier)
# ============================================================================
 
# Auto-login after social auth
SOCIALACCOUNT_AUTO_SIGNUP = True
 
# Google Provider Settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'APP': {
            'client_id': GOOGLE_OAUTH_CLIENT_ID,
            'secret': GOOGLE_OAUTH_CLIENT_SECRET,
            'key': ''
        }
    }
}
 
# ============================================================================
# ALTERNATIVE: MANUAL GOOGLE OAUTH (without django-allauth)
# ============================================================================
# Use the GoogleAuthService from accounts/services.py
 
# Requires: pip install google-auth

# ============================================================================
# CORS CONFIGURATION (for AJAX requests from frontend)
# ============================================================================
 
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://yourdomain.com',
]