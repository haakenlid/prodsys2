# -*- coding: utf-8 -*-
""" Django settings for universitas_no project. """

from os.path import dirname
import django.conf.global_settings as DEFAULT_SETTINGS
from django.utils.translation import ugettext_lazy as _
from utils.setting_helpers import (
    environment_variable, join_path, load_json_file)
from .logging_settings import *

SITE_URL = environment_variable('SITE_URL')
DEBUG = TEMPLATE_DEBUG = False
ALLOWED_HOSTS = environment_variable('ALLOWED_HOSTS').split()

STATIC_URL = "http://{host}/{static}/".format(
    host=AWS_S3_CUSTOM_DOMAIN, static=STATIC_ROOT, )

MEDIA_URL = "http://{host}/{media}/".format(
    host=AWS_S3_CUSTOM_DOMAIN, media=MEDIA_ROOT, )

INSTALLED_APPS = [  # CUSTOM APPS

]

INSTALLED_APPS = [  # THIRD PARTY APPS
    'django_extensions',
    'sorl.thumbnail',
    'raven.contrib.django.raven_compat',
    'storages',
] + INSTALLED_APPS

INSTALLED_APPS = [  # CORE APPS
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
] + INSTALLED_APPS

MIDDLEWARE_CLASSES = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Prodsys for universitas.
# PRODSYS_USER = environment_variable('PRODSYS_USER')
# PRODSYS_PASSWORD = environment_variable('PRODSYS_PASSWORD')
# PRODSYS_URL = environment_variable('PRODSYS_URL')

ROOT_URLCONF = 'core.urls'
SECRET_KEY = environment_variable('SECRET_KEY')
SITE_URL = environment_variable('SITE_URL')
WSGI_APPLICATION = 'core.wsgi.application'

LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_URL = '/'

# SORL THUMBNAILS
THUMBNAIL_KVSTORE = 'sorl.thumbnail.kvstores.redis_kvstore.KVStore'
THUMBNAIL_ENGINE = 'apps.photo.thumb_utils.CloseCropEngine'
THUMBNAIL_QUALITY = 75
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o6770
FILE_UPLOAD_PERMISSIONS = 0o664

# With boto and aman s3, we don't check if file exist.
# Automatic overwrite if not found in cache key
THUMBNAIL_FORCE_OVERWRITE = True
THUMBNAIL_PREFIX = 'thumb-cache/'
THUMBNAIL_REDIS_DB = 1
THUMBNAIL_KEY_PREFIX = SITE_URL
THUMBNAIL_URL_TIMEOUT = 3

# DATABASE
DATABASE_ROUTERS = ['apps.legacy_db.router.ProdsysRouter']
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': environment_variable('DB_NAME'),
        'USER': environment_variable('DB_USER'),
        'PASSWORD': environment_variable('DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5432',       # Set to empty string for default.
    },
    'prodsys': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': environment_variable('PRODSYS_DB_NAME'),
        'USER': environment_variable('PRODSYS_DB_USER'),
        'PASSWORD': environment_variable('PRODSYS_DB_PASSWORD'),
        'HOST': environment_variable('PRODSYS_DB_HOST'),
        'PORT': '',       # Set to empty string for default.
    }
}
# CACHE
CACHE_MIDDLEWARE_KEY_PREFIX = SITE_URL
CACHES = {
    'default': {
        'BACKEND': 'redis_cache.RedisCache',
        'LOCATION': 'localhost:6379',
        'OPTIONS': {
            'DB': 0,
            'MAX_ENTRIES': 1000,
            'PARSER_CLASS': 'redis.connection.HiredisParser',
            'CONNECTION_POOL_CLASS': 'redis.BlockingConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': 50,
                'timeout': 20,
            }
        },
    },
}

# SENTRY
RAVEN_CONFIG = {'dsn': environment_variable('RAVEN_DSN'), }
SENTRY_CLIENT = 'raven.contrib.django.raven_compat.DjangoClient'

# AMAZON WEB SERVICES
# AWS_STORAGE_BUCKET_NAME = environment_variable('AWS_STORAGE_BUCKET_NAME')
# AWS_ACCESS_KEY_ID = environment_variable('AWS_ACCESS_KEY_ID')
# AWS_SECRET_ACCESS_KEY = environment_variable('AWS_SECRET_ACCESS_KEY')
# AWS_S3_HOST = 's3.eu-central-1.amazonaws.com'
# AWS_S3_CUSTOM_DOMAIN = AWS_STORAGE_BUCKET_NAME  # cname
# AWS_S3_SECURE_URLS = False
# AWS_S3_USE_SSL = False
# AWS_S3_FILE_BUFFER_SIZE = 5242880
# Buffer size is used to calculate md5 hash for AWS mulitpart uploads
# if changed, md5 hashes for large files might be wrong

STATIC_ROOT = 'static'
MEDIA_ROOT = 'media'
# STATICFILES_STORAGE = 'utils.aws_custom_storage.StaticStorage'
# DEFAULT_FILE_STORAGE = 'utils.aws_custom_storage.MediaStorage'
# THUMBNAIL_STORAGE = 'utils.aws_custom_storage.ThumbStorage'

# FOLDERS
# source code folder
BASE_DIR = environment_variable('SOURCE_FOLDER')
# outside of repo
PROJECT_DIR = dirname(BASE_DIR)

# GULP FILE REVISIONS
GULP_FILEREVS = load_json_file(
    join_path(PROJECT_DIR, 'build', 'rev-manifest.json'))

# Django puts generated translation files here.
LOCALE_PATHS = [join_path(BASE_DIR, 'translation'), ]
# Extra path to collect static assest such as javascript and css
STATICFILES_DIRS = [join_path(PROJECT_DIR, 'build'), ]
# Project wide fixtures to be loaded into database.
FIXTURE_DIRS = [join_path(BASE_DIR, 'fixtures'), ]
# Project wide django template files
TEMPLATE_DIRS = [join_path(BASE_DIR, 'templates'), ]
# Look for byline images here
BYLINE_PHOTO_DIR = '/srv/fotoarkiv_universitas/byline/'
STAGING_ROOT = '/srv/fotoarkiv_universitas/'


# INTERNATIONALIZATION
LANGUAGE_CODE = 'nb'
LANGUAGES = [
    ('nb', _('Norwegian Bokmal')),
]

TIME_ZONE = 'Europe/Oslo'
USE_I18N = True  # Internationalisation (string translation)
USE_L10N = True  # Localisation (numbers and stuff)
USE_TZ = True  # Use timezone
DATE_FORMAT = 'j. F, Y'
DATETIME_FORMAT = 'Y-m-d H:i'
SHORT_DATE_FORMAT = 'Y-m-d'
SHORT_DATETIME_FORMAT = 'y-m-d H:i'
TIME_INPUT_FORMATS = ('%H:%M', '%H', '%H:%M:%S', '%H.%M')

TEMPLATE_CONTEXT_PROCESSORS = DEFAULT_SETTINGS.TEMPLATE_CONTEXT_PROCESSORS + (
    'django.core.context_processors.request',
    'apps.issues.context_processors.issues',
    'apps.contributors.context_processors.staff',
)
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
]
