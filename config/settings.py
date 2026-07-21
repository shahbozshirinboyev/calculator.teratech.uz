"""
Django settings for config project.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-local-dev-only")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


DEBUG = env_bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", default="*")

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

# AI Studio preview platform integration
app_url = os.environ.get("APP_URL")
if app_url:
    from urllib.parse import urlparse
    parsed = urlparse(app_url)
    domain = parsed.netloc
    if domain:
        # Add the original domain
        if domain not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(domain)
        origin = f"{parsed.scheme}://{domain}"
        if origin not in CSRF_TRUSTED_ORIGINS:
            CSRF_TRUSTED_ORIGINS.append(origin)
        
        # Also support the "ais-pre" counterpart if it's "ais-dev"
        if "ais-dev-" in domain:
            pre_domain = domain.replace("ais-dev-", "ais-pre-")
            if pre_domain not in ALLOWED_HOSTS:
                ALLOWED_HOSTS.append(pre_domain)
            pre_origin = f"{parsed.scheme}://{pre_domain}"
            if pre_origin not in CSRF_TRUSTED_ORIGINS:
                CSRF_TRUSTED_ORIGINS.append(pre_origin)
        # Also support the "ais-dev" counterpart if it's "ais-pre"
        elif "ais-pre-" in domain:
            dev_domain = domain.replace("ais-pre-", "ais-dev-")
            if dev_domain not in ALLOWED_HOSTS:
                ALLOWED_HOSTS.append(dev_domain)
            dev_origin = f"{parsed.scheme}://{dev_domain}"
            if dev_origin not in CSRF_TRUSTED_ORIGINS:
                CSRF_TRUSTED_ORIGINS.append(dev_origin)

ng_allowed_hosts = os.environ.get("NG_ALLOWED_HOSTS")
if ng_allowed_hosts:
    for host in ng_allowed_hosts.split(","):
        host = host.strip()
        if host and host not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(host)
        # Check dev/pre equivalents for ng_allowed_hosts too
        if "ais-dev-" in host:
            pre_host = host.replace("ais-dev-", "ais-pre-")
            if pre_host not in ALLOWED_HOSTS:
                ALLOWED_HOSTS.append(pre_host)
        elif "ais-pre-" in host:
            dev_host = host.replace("ais-pre-", "ais-dev-")
            if dev_host not in ALLOWED_HOSTS:
                ALLOWED_HOSTS.append(dev_host)

# Always allow * in ALLOWED_HOSTS during preview to prevent any 400 Bad Request
if app_url or ng_allowed_hosts:
    if "*" not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append("*")

# AI Studio preview platform (iframe) and production cookie integration
if app_url or ng_allowed_hosts:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "None"
    CSRF_COOKIE_SAMESITE = "None"
else:
    if not DEBUG:
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
        SESSION_COOKIE_SECURE = True
        CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Lax"
    CSRF_COOKIE_SAMESITE = "Lax"

# CSRF cookie'ni JS orqali o'qilishini ta'minlash (kerak emas lekin xavfsiz)
CSRF_COOKIE_HTTPONLY = False

INSTALLED_APPS = [
    "products",
    "calculator",
    "monitors",
    "printers",
    "orders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Auth
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"
