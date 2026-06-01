# cPanel ga deploy qilish — AIO Calculator

## 1. Serverga yuklash

ZIP qilib cPanel **File Manager** orqali yuklang yoki Git orqali clone qiling.

**Yuklanishi kerak:**
```
calculator/
config/
products/
templates/          ← 404.html shu yerda
manage.py
passenger_wsgi.py
requirements.txt
```

**Yuklanmasin:**
```
.env                ← maxfiy, hech qachon yuklamang
db.sqlite3          ← serverda migrate bilan yaratiladi
staticfiles/        ← serverda collectstatic bilan yig'iladi
__pycache__/
.venv/
Pipfile
Pipfile.lock
```

---

## 2. Python ilovasini yaratish

cPanel → **Setup Python App** → **Create Application**

| Maydon | Qiymat |
|--------|--------|
| Python version | 3.11 |
| Application root | `calculator.teratech.uz` |
| Application URL | `/` |
| Application startup file | `passenger_wsgi.py` |
| Application entry point | `application` |

---

## 3. Environment variables

cPanel → Setup Python App → **Environment variables** bo'limiga qo'shing:

```
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<uzun-tasodifiy-kalit>
DJANGO_ALLOWED_HOSTS=calculator.teratech.uz,www.calculator.teratech.uz
DJANGO_CSRF_TRUSTED_ORIGINS=https://calculator.teratech.uz,https://www.calculator.teratech.uz
```

`DJANGO_SECRET_KEY` generatsiya qilish:
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## 4. Paketlar o'rnatish va migratsiya

cPanel → Python App → **Enter to the virtual environment**, keyin:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

---

## 5. Ruxsatlar

SQLite uchun loyiha papkasi **yozish** huquqiga ega bo'lishi kerak:
```bash
chmod 755 ~/calculator.teratech.uz
chmod 664 ~/calculator.teratech.uz/db.sqlite3
```

---

## 6. Ilovani qayta ishga tushirish

Python App sahifasida **Restart** tugmasini bosing.

Brauzerda oching: `https://calculator.teratech.uz`

---

## 7. Tekshirish ro'yxati

- [ ] Bosh sahifa ochiladi va login so'raladi
- [ ] Login ishlaydi
- [ ] Dark/light mode ishlaydi
- [ ] Dollar kursi saqlanadi
- [ ] Hisob-kitob saqlanadi
- [ ] Admin panel: `https://calculator.teratech.uz/admin/`
- [ ] HTTPS ishlaydi (CSRF xatosi yo'q)
- [ ] 404 sahifasi chiroyli ko'rinadi

---

## Muammolar

**500 xato**
```
# cPanel → Errors yoki passenger.log ni tekshiring
# Vaqtincha debug yoqish:
DJANGO_DEBUG=True
# Xatoni ko'rgach yana False qiling
```

**Static fayllar (admin CSS) yo'q**
```bash
python manage.py collectstatic --noinput
```

**CSRF xato**
- `DJANGO_CSRF_TRUSTED_ORIGINS` da `https://` bilan to'liq domen bo'lsin

**Mavjud bazani ko'chirish**
- Lokal `db.sqlite3` ni serverdagi loyiha papkasiga yuklang
