"""
Django settings for config project.
"""

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-local-dev-only")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name)
    if not raw:
        return default
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = BASE_DIR / path
    return path


DEBUG = env_bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", default="127.0.0.1,localhost")

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
        "ENGINE": os.environ.get("DJANGO_DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": str(env_path("DJANGO_DB_NAME", BASE_DIR / "db.sqlite3")),
        "USER": os.environ.get("DJANGO_DB_USER", ""),
        "PASSWORD": os.environ.get("DJANGO_DB_PASSWORD", ""),
        "HOST": os.environ.get("DJANGO_DB_HOST", ""),
        "PORT": os.environ.get("DJANGO_DB_PORT", ""),
        "OPTIONS": {},
    }
}

db_conn_max_age = os.environ.get("DJANGO_DB_CONN_MAX_AGE")
if db_conn_max_age:
    DATABASES["default"]["CONN_MAX_AGE"] = int(db_conn_max_age)

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
STATIC_ROOT = env_path("DJANGO_STATIC_ROOT", BASE_DIR / "staticfiles")
MEDIA_URL = "/media/"
MEDIA_ROOT = env_path("DJANGO_MEDIA_ROOT", BASE_DIR / "media")
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

if not DEBUG:
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", default=False)
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_SECURE_HSTS_SECONDS", "0"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False)
    SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", default=False)
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = os.environ.get("DJANGO_SECURE_REFERRER_POLICY", "same-origin")
    USE_X_FORWARDED_HOST = env_bool("DJANGO_USE_X_FORWARDED_HOST", default=True)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Auth
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/login/"
