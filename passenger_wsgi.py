"""
cPanel Passenger entry point.
Place this file in the application root (same folder as manage.py).
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

APP_ROOT = os.path.dirname(os.path.abspath(__file__))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

# .env faylni yukla
load_dotenv(Path(APP_ROOT) / ".env")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()