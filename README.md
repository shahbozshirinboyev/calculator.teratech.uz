# Calculator Teratech UZ

Django asosidagi ichki calculator va buyurtma boshqaruv tizimi.

## Texnologiyalar

- Python 3.11
- Django 5.2
- WhiteNoise
- SQLite (default)

## Lokal ishga tushirish

1. Virtual environment yarating va aktiv qiling
2. Paketlarni o'rnating:

```bash
pip install -r requirements.txt
```

3. `.env.example` dan nusxa olib `.env` yarating
4. Migratsiyalarni ishlating:

```bash
python manage.py migrate
```

5. Static fayllarni yig'ing:

```bash
python manage.py collectstatic --noinput
```

6. Serverni ishga tushiring:

```bash
python manage.py runserver
```

## Muhit o'zgaruvchilari

Asosiy o'zgaruvchilar:

```text
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DJANGO_CSRF_TRUSTED_ORIGINS=
DJANGO_DB_ENGINE=django.db.backends.sqlite3
DJANGO_DB_NAME=db.sqlite3
DJANGO_STATIC_ROOT=staticfiles
DJANGO_MEDIA_ROOT=media
```

To'liq deploy yo'riqnomasi:

- [DEPLOY_CPANEL.md](file:///c:/Users/shahb/OneDrive/Desktop/calculator.teratech.uz/DEPLOY_CPANEL.md)
