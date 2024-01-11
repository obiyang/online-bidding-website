"""
Django settings for group1_project project.

Generated by 'django-admin startproject' using Django 4.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
import pymysql # noqa:402
import os
from django.utils import timezone

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-#y@cphs@1c7i!fyp*s&(9r-t1-ybwc7a^su1$duw&3wn5bpj=m"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "debug_toolbar",
    'channels',
    'storages',

    "auctionHouse"
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = 'login'

INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]

ROOT_URLCONF = "group1_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR/ "templates"],
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

WSGI_APPLICATION = "group1_project.wsgi.application"


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
pymysql.version_info = (1, 4, 6, 'final', 0) # change mysqlclient version
pymysql.install_as_MySQLdb
if os.getenv('GAE_APPLICATION', None):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": "onlinebiddingdemo",
            "USER": "byang",
            "PASSWORD": "660220",
            "HOST": "/cloudsql/my-project-00274059:us-west1:onlinebiddingdemo",
        }
    }


else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": "onlinebiddingdemo",
            "USER": "byang",
            "PASSWORD": "660220",
            "HOST": "34.118.199.201",
            "PORT": "3306",
        }
    }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

now = timezone.now

TIME_ZONE = "America/Los_Angeles"

USE_I18N = True

USE_TZ = False

# Configure Django to use GCS for media file storage
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_BUCKET_NAME = 'onlinebiddingdemobucket'
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_ROOT = "static"
STATIC_URL = "/static/"
#MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/media/auction_images/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

GS_QUERYSTRING_AUTH = False

# 设置环境变量
#os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/binyang/Documents/group1_folder 2/db-group1-402300-ca03e56dc003.json'
if os.getenv('GAE_ENV', '').startswith('standard'):
    # GAE 环境，使用默认服务账户
    # 在这里不需要设置 GOOGLE_APPLICATION_CREDENTIALS
    pass
else:
    # 非 GAE 环境，比如本地开发环境
    # path need to change in order to run locally
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/binyang/Documents/group1_folder 2/db-group1-402300-ca03e56dc003.json'

LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}


