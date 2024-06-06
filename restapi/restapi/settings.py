import json
from pathlib import Path
import warnings
from django.utils.deprecation import RemovedInDjango50Warning
import mimetypes
import os

mimetypes.add_type("text/css", ".css", True)

warnings.filterwarnings(
    'ignore',
    category=RemovedInDjango50Warning,
    message="MySQL does not support unique constraints with conditions."
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-o-p5ev6b+u!d#zb37bfen#bh$$7qy#ok7g(!gc(m)%4eia3wax'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'sslserver',

    "rest_framework",
    "rest_framework.authtoken",

    "django.contrib.sites",
    "dj_rest_auth",
    "dj_rest_auth.registration",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google", # 구글 소셜
    'allauth.socialaccount.providers.github',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
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
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'django_database',
        'USER': 'root',
        'PASSWORD': 'rlaqjatn256^',
        'HOST': 'localhost',
        'PORT': '3306',
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
)

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'ko-kr'

TIME_ZONE = 'Asia/Seoul'

SITE_ID = 1

USE_I18N = True

USE_L10N = True

USE_TZ = True

X_FRAME_OPTIONS = 'SAMEORIGIN'  # 같은 출처의 도메인에서만 <iframe> 내 로딩을 허용

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

SESSION_COOKIE_SAMESITE = 'Lax'  # 현재 도메인과 같은 도메인에서만 쿠키를 전송
CSRF_COOKIE_SAMESITE = 'Lax'     # 현재 도메인과 같은 도메인에서만 쿠키를 전송
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# config.json 파일 경로 설정
BASE_DIR = Path(__file__).resolve().parent.parent
config_path = BASE_DIR / 'restapi/config.json'

# config.json 파일 로드
with open(config_path, 'r') as file:
    config = json.load(file)

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static'),]

IPSTACK_KEY = config['IPSTACK_KEY']
WEATHER_API_KEY = config['WEATHER_API_KEY']