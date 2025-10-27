
from pathlib import Path
import os
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-j+fa$j-w-x7ua4upzterye(*1g7j5clih!9ym)0oo$12wf_bf%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'bluecode2004.pythonanywhere.com']


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'admin_dashboard',
    'dashboard_admin',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ProyekBarokah.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'admin_dashboard.context_processors.notification_cart_context',
                'dashboard_admin.context_processors.admin_crm_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'ProyekBarokah.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'id-ID'

TIME_ZONE = 'Asia/Makassar' 

USE_I18N = True

USE_TZ = True

# STATIC_URL adalah URL yang digunakan untuk mereferensikan file statis.
STATIC_URL = '/static/'

# STATICFILES_DIRS adalah direktori tambahan tempat Django harus mencari file statis.
# Tambahkan path ke folder 'static' yang baru Anda buat.
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# STATIC_ROOT adalah direktori tempat file statis dikumpulkan untuk produksi.
# Jangan tambahkan file statis di sini secara manual.
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# URL yang digunakan saat mereferensikan file media.
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

# PENTING: Pastikan variabel DEBUG terdefinisi dengan benar

if DEBUG:
    # Untuk Development/Testing (Tidak mengirim email, hanya mencegah error)
    EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
else:
    # Untuk Production (Ganti dengan kredensial SMTP PythonAnywhere yang valid)
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.hostanda.com' # Placeholder
    EMAIL_PORT = 587 # Placeholder
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'user@domain.com' # Placeholder
    EMAIL_HOST_PASSWORD = 'password-anda' # Placeholder

DEFAULT_FROM_EMAIL = 'admin@barokah.com'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'admin_dashboard.Admin'
