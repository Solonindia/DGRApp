from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Azure Storage Configuration
AZURE_STORAGE_CONNECTION_STRING = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
AZURE_ACCOUNT_NAME = os.getenv('AZURE_ACCOUNT_NAME')
AZURE_ACCOUNT_KEY = os.getenv('AZURE_ACCOUNT_KEY')
AZURE_CONTAINER = os.getenv('AZURE_CONTAINER')

# Use Azure Blob Storage for file uploads
DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'

# Other Django settings (e.g., Secret Key)
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = False
ALLOWED_HOSTS = [
    'oandm-ghhwf3ftcqhtf6g5.eastus-01.azurewebsites.net',
    '127.0.0.1',
    'localhost',
    '169.254.130.4',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'storages',
    'demoapp',
    'gatepass',
    'Inventory',
    'report'
]

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    # Add this line:
    'demodjango.middleware.no_cache.NoCacheForHtmlMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'demodjango.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'),],
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

WSGI_APPLICATION = 'demodjango.wsgi.application'

CSRF_TRUSTED_ORIGINS = [
    'https://oandm-ghhwf3ftcqhtf6g5.eastus-01.azurewebsites.net',
    'http://oandm-ghhwf3ftcqhtf6g5.eastus-01.azurewebsites.net',
    'http://localhost',

]

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': '3306',
    }
}

# Password validation
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

# LOGIN_URL = '/home/'
# settings.py
LOGIN_URL = '/user/login/'              # default for auth redirects
LOGOUT_REDIRECT_URL = '/user/login/'    # default after logout

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 3600  # 1 hour for session expiration
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Automatically expire sessions when the browser is closed

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'  # or any other time zone you are using

USE_I18N = True
USE_L10N = True
TIME_ZONE = 'Asia/Kolkata'
USE_TZ = True

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")


if DEBUG:
    # Local setup
    STATIC_URL = '/static/'
    # STATIC_ROOT = BASE_DIR / 'static'
    # LOGOUT_REDIRECT_URL = '/home/'
    STATICFILES_DIRS = [BASE_DIR / 'static']   # ← for local dev


    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
else:
    # Azure setup
    STATIC_URL = f'https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/{AZURE_CONTAINER}/'
    STATICFILES_STORAGE = 'storages.backends.azure_storage.AzureStorage'
    DEFAULT_FILE_STORAGE = 'storages.backends.azure_storage.AzureStorage'
    # LOGOUT_REDIRECT_URL = '/home/'


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.office365.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER