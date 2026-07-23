# cPanel ga deploy qilish

Bu loyiha `cPanel -> Setup Python App -> Passenger` sxemasi uchun moslangan.

## 1. Serverga yuklanadigan fayllar

Serverga loyiha rootini yuklang. Asosiy kerakli fayllar:

```text
calculator/
config/
monitors/
orders/
printers/
products/
templates/
manage.py
passenger_wsgi.py
requirements.txt
.env.example
```

Yuklamaslik tavsiya qilinadi:

```text
.git/
.venv/
__pycache__/
staticfiles/
media/
db.sqlite3
```

## 2. cPanel da Python App yaratish

`Setup Python App` ichida quyidagicha yarating:

| Maydon | Qiymat |
| --- | --- |
| Python version | `3.11` |
| Application root | masalan `calculator.teratech.uz` |
| Application URL | `/` |
| Application startup file | `passenger_wsgi.py` |
| Application entry point | `application` |

## 3. Environment variables

Eng kamida quyidagilarni kiriting:

```text
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<uzun-maxfiy-kalit>
DJANGO_ALLOWED_HOSTS=calculator.teratech.uz,www.calculator.teratech.uz
DJANGO_CSRF_TRUSTED_ORIGINS=https://calculator.teratech.uz,https://www.calculator.teratech.uz
DJANGO_STATIC_ROOT=/home/USERNAME/calculator.teratech.uz/staticfiles
DJANGO_MEDIA_ROOT=/home/USERNAME/calculator.teratech.uz/media
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_USE_X_FORWARDED_HOST=True
```

`DJANGO_SECRET_KEY` generatsiya qilish:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### SQLite varianti

Agar SQLite ishlatsangiz, qo'shimcha:

```text
DJANGO_DB_ENGINE=django.db.backends.sqlite3
DJANGO_DB_NAME=/home/USERNAME/calculator.teratech.uz/db.sqlite3
```

### MySQL varianti

Agar cPanel MySQL bazasini ishlatsangiz:

```text
DJANGO_DB_ENGINE=django.db.backends.mysql
DJANGO_DB_NAME=cpanel_db_name
DJANGO_DB_USER=cpanel_db_user
DJANGO_DB_PASSWORD=strong-password
DJANGO_DB_HOST=localhost
DJANGO_DB_PORT=3306
DJANGO_DB_CONN_MAX_AGE=60
```

## 4. Virtual environment ichida buyruqlar

`Enter to the virtual environment` ni bosing va quyidagilarni ishlating:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py check --deploy
```

## 5. Ruxsatlar

### SQLite uchun

```bash
mkdir -p media staticfiles
touch db.sqlite3
chmod 755 ~/calculator.teratech.uz
chmod 775 ~/calculator.teratech.uz/media
chmod 775 ~/calculator.teratech.uz/staticfiles
chmod 664 ~/calculator.teratech.uz/db.sqlite3
```

### MySQL uchun

`db.sqlite3` kerak bo'lmaydi, lekin `media/` va `staticfiles/` papkalari yozishga ruxsatli bo'lsin.

## 6. Restart

Python App sahifasida `Restart` tugmasini bosing.

Shundan keyin tekshiring:

- `https://calculator.teratech.uz/login/`
- `https://calculator.teratech.uz/admin/`

## 7. Tekshirish ro'yxati

- [ ] Login sahifasi ochiladi
- [ ] Login ishlaydi
- [ ] Buyurtma yaratish ishlaydi
- [ ] Buyurtma ro'yxati ishlaydi
- [ ] Admin panel ochiladi
- [ ] Static fayllar yuklanadi
- [ ] CSRF xato yo'q
- [ ] Light/dark mode ishlaydi

## 8. Tez-tez uchraydigan muammolar

### 500 Internal Server Error

- cPanel `Errors` bo'limini tekshiring
- `passenger_wsgi.py` yo'li to'g'ri ekanini tekshiring
- vaqtincha `DJANGO_DEBUG=True` qilib xatoni ko'ring, keyin yana `False` ga qaytaring

### Admin CSS yo'q

```bash
python manage.py collectstatic --noinput
```

### `DisallowedHost`

- `DJANGO_ALLOWED_HOSTS` ichida domen aniq yozilgan bo'lsin

### CSRF xato

- `DJANGO_CSRF_TRUSTED_ORIGINS` ichida `https://` bilan to'liq origin bo'lsin

### SQLite yozmayapti

- `db.sqlite3` va loyiha papkasi yozishga ruxsatli ekanini tekshiring

### Static yoki media yo'l ishlamayapti

- `DJANGO_STATIC_ROOT` va `DJANGO_MEDIA_ROOT` absolute path bo'lsa yaxshiroq
