"""
cPanel Passenger entry point.
Place this file in the application root (same folder as manage.py).
"""
import os
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

APP_ROOT = Path(__file__).resolve().parent
APP_ROOT_STR = str(APP_ROOT)

if APP_ROOT_STR not in sys.path:
    sys.path.insert(0, APP_ROOT_STR)

load_dotenv(APP_ROOT / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
