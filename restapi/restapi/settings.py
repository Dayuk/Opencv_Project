from pathlib import Path
import warnings
from django.utils.deprecation import RemovedInDjango50Warning
import mimetypes
import os
import torch

from .secrets import *

mimetypes.add_type("text/css", ".css", True)

warnings.filterwarnings(
    'ignore',
    category=RemovedInDjango50Warning,
    message="MySQL does not support unique constraints with conditions."
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# # Set HSTS (HTTP Strict Transport Security)
# SECURE_HSTS_SECONDS = 31536000  # 1 year
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# # Redirect HTTP to HTTPS
# SECURE_SSL_REDIRECT = True

IPSTACK_KEY = IPSTACK_KEY
WEATHER_API_KEY = WEATHER_API_KEY
WEATHER_API_KEY2 = WEATHER_API_KEY2

GOOGLE_CLIENT_ID = GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI = GOOGLE_REDIRECT_URI

GH_CLIENT_ID = GH_CLIENT_ID
GH_CLIENT_SECRET = GH_CLIENT_SECRET
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = True
DEBUG = bool( os.environ.get('DJANGO_DEBUG', True) )

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    "rest_framework",
    "rest_framework_api_key",
    "rest_framework.authtoken",
    "channels",
    'django_secrets',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.github',
    "restapi",
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'allauth.account.middleware.AccountMiddleware',

    'corsheaders.middleware.CorsMiddleware',
]

CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

ROOT_URLCONF = 'restapi.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'restapi.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': ENGINE,
        'NAME': NAME,
        'USER': USER,
        'PASSWORD': PASSWORD,
        'HOST': HOST,
        'PORT': PORT,
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',  # Django 기본 인증 백엔드
    'allauth.account.auth_backends.AuthenticationBackend',  # django-allauth 인증 백엔드
    'channels_redis.core.RedisChannelLayer',
)

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'ko-kr'

TIME_ZONE = 'Asia/Seoul'

SITE_ID = 1

USE_I18N = True

USE_L10N = True

USE_TZ = True

# 이메일을 필수로 설정
ACCOUNT_EMAIL_REQUIRED = True
# 이메일이 유니크한지 확인
ACCOUNT_UNIQUE_EMAIL = True
# 사용자 이름을 필수로 설정
ACCOUNT_USERNAME_REQUIRED = True

AUTH_USER_MODEL = 'restapi.CustomUser'

REDIRECT_URL = '/'

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static'),]

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

SESSION_COOKIE_SAMESITE = 'Lax'  # 현재 도메인과 같은 도메인에서만 쿠키를 전송
CSRF_COOKIE_SAMESITE = 'Lax'     # 현재 도메인과 같은 도메인에서만 쿠키를 전송
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': GOOGLE_CLIENT_ID,
            'secret': GOOGLE_CLIENT_SECRET,
            'key': ''
        }
    },
    'github': {
        'APP': {
            'client_id': GH_CLIENT_ID,
            'secret': GH_CLIENT_SECRET,
            'key': ''
        }
    }
}

SOCIALACCOUNT_LOGIN_ON_GET = True

ASGI_APPLICATION = 'restapi.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework_api_key.permissions.HasAPIKey",
    ]
}

device = 'cuda' if torch.cuda.is_available() else 'cpu'
MODEL = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True).to(device)
MODEL.eval()
