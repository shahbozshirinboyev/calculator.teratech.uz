# cPanel ga deploy qilish (AIO Calculator)

## 1. Tayyor fayllarni yuklash

ZIP qiling va cPanel **File Manager** orqali serverga yuklang (masalan: `calculator.teratech.uz` papkasi).

**Yuklanishi kerak:**
- `calculator/`, `config/`, `products/`
- `manage.py`, `passenger_wsgi.py`, `requirements.txt`

**Yuklanmasin:**
- `.env` (maxfiy)
- `db.sqlite3` (birinchi marta serverda yaratiladi)
- `staticfiles/` (serverda `collectstatic` bilan yig'iladi)
- `__pycache__/`, `.venv/`, `runserver*.log`

---

## 2. Python ilovasini yaratish

cPanel → **Setup Python App** → **Create Application**

| Maydon | Qiymat |
|--------|--------|
| Python version | 3.11 yoki 3.12 |
| Application root | `calculator.teratech.uz` (loyiha papkasi) |
| Application URL | `/` yoki subdomain |
| Application startup file | `passenger_wsgi.py` |
| Application entry point | `application` |

**Environment variables** (`.env.example` dan):

```
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<uzun-tasodifiy-kalit>
DJANGO_ALLOWED_HOSTS=calculator.teratech.uz,www.calculator.teratech.uz
DJANGO_CSRF_TRUSTED_ORIGINS=https://calculator.teratech.uz,https://www.calculator.teratech.uz
```

`DJANGO_SECRET_KEY` uchun terminalda:
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## 3. Paketlar va migratsiya

cPanel → Python App → **Enter to the virtual environment**, keyin:

```bash
cd ~/calculator.teratech.uz
pip install -r requirements.txt
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

(`createsuperuser` — admin panel uchun)

---

## 4. Ruxsatlar

`db.sqlite3` va loyiha papkasi **yozish** huquqiga ega bo'lishi kerak (SQLite uchun).

Agar `db.sqlite3` yo'q bo'lsa, `migrate` avtomatik yaratadi.

---

## 5. Ilovani qayta ishga tushirish

Python App sahifasida **Restart** tugmasini bosing.

Brauzerda oching: `https://calculator.teratech.uz`

---

## 6. Tekshirish ro'yxati

- [ ] Bosh sahifa (kalkulyator) ochiladi
- [ ] Admin: `https://calculator.teratech.uz/admin/`
- [ ] Dollar kursi saqlanadi
- [ ] Hisob-kitob saqlanadi (Saved Calculations)
- [ ] HTTPS ishlayapti (CSRF xatosi bo'lmasa, `DJANGO_CSRF_TRUSTED_ORIGINS` to'g'ri)

---

## Muammolar

**500 xato**
- cPanel → Errors yoki `passenger.log` ni tekshiring
- `DJANGO_DEBUG=True` vaqtincha qo'yib xatoni ko'ring (keyin yana `False` qiling)

**Static (admin CSS) yo'q**
```bash
python manage.py collectstatic --noinput
```

**CSRF xato**
- `DJANGO_CSRF_TRUSTED_ORIGINS` da `https://` bilan to'liq domen bo'lsin

**Mavjud bazani ko'chirish**
- Lokal `db.sqlite3` ni serverdagi loyiha papkasiga yuklang (eski ma'lumotlar saqlanadi)
