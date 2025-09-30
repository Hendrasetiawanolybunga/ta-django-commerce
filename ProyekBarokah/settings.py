
from pathlib import Path
import os
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-j+fa$j-w-x7ua4upzterye(*1g7j5clih!9ym)0oo$12wf_bf%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'import_export',
    'admin_dashboard',
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

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'admin_dashboard.Admin'
JAZZMIN_SETTINGS = {
    "site_title": "Barokah Jaya Beton",
    "site_header": "Barokah Jaya Beton",
    "site_brand": "Barokah Jaya Beton",
    "site_logo": None,
    "hide_models": [
        "auth.Group",
    ],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "admin_dashboard.Pelanggan": "fas fa-user-friends",
        "admin_dashboard.Kategori": "fas fa-tags",
        "admin_dashboard.DiskonPelanggan": "fas fa-percent",
        "admin_dashboard.Produk": "fas fa-boxes",
        "admin_dashboard.Transaksi": "fas fa-shopping-cart",
        "admin_dashboard.DetailTransaksi": "fas fa-receipt",
        "admin_dashboard.Notifikasi": "fas fa-bell",
        "admin_dashboard.admin": "fas fa-user",
    },
    "order_with_respect_to": [
        "admin_dashboard.Produk",
        "admin_dashboard.Kategori",
        "admin_dashboard.DiskonPelanggan",
        "admin_dashboard.Notifikasi",
        "admin_dashboard.Transaksi",
        "admin_dashboard.DetailTransaksi",
        "admin_dashboard.Pelanggan",
    ],
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-success",
    "accent": "accent-navy",
    "navbar": "navbar-success navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-light-success",
    "sidebar_nav_small_text": True,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,
    "theme": "yeti",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    },
    "actions_sticky_top": False
}



