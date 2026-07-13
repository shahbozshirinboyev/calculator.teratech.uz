# Requirements: Currency Conversion Enhancement

## 1. Kurs Tarixi Boshqaruvi

### 1.1 Kurs Tarixi Saqlash
Tizim har bir dollar kursi o'zgarishini tarixiy yozuv sifatida saqlashi kerak.

**Acceptance Criteria:**
- Har bir kurs o'zgarishi alohida yozuv sifatida saqlanadi
- Har bir yozuvda: kurs qiymati, o'rnatilgan sana-vaqt, o'rnatgan foydalanuvchi ko'rsatiladi
- Tarixiy yozuvlar o'chirilmaydi (faqat qo'shiladi)
- Yangi kurs kiritilganda avtomatik yangi tarixiy yozuv yaratiladi

### 1.2 Joriy Kurs Olish
Tizim har doim eng so'nggi (active) dollar kursini ishlatishi kerak.

**Acceptance Criteria:**
- CalculatorSettings.usd_rate har doim eng so'nggi kurs bilan sinxronlashgan
- Joriy kurs null bo'lishi mumkin emas
- Kurs 0 dan katta bo'lishi kerak
- Tizim joriy kursni olib kelishda eng so'nggi yozuvni ishlatadi

### 1.3 Kurs Tarixi Ko'rsatish
Foydalanuvchilar kurs o'zgarish tarixini ko'rish imkoniyatiga ega bo'lishi kerak.

**Acceptance Criteria:**
- Tarix teskari xronologik tartibda ko'rsatiladi (eng yangi birinchi)
- Har bir yozuvda: kurs, sana-vaqt, foydalanuvchi ko'rsatiladi
- Tarih sahifalanadi (pagination) - har bir sahifada maksimal 50 ta yozuv
- Kurs qiymati formatlangan ko'rinishda (masalan: 12,650.00)

## 2. Kurs Validatsiya

### 2.1 Kurs Qiymat Validatsiyasi
Yangi kurs kiritishda qiymat to'g'riligini tekshirish kerak.

**Acceptance Criteria:**
- Kurs 0 dan katta bo'lishi kerak
- Kurs 100 dan katta bo'lishi kerak (minimal mantiqiy qiymat)
- Kurs 1,000,000 dan kichik bo'lishi kerak (maksimal mantiqiy qiymat)
- Kurs faqat musbat raqam bo'lishi kerak
- Kurs eng ko'p 2 ta kasr raqamga ega bo'lishi mumkin

### 2.2 Kurs Format Validatsiyasi
Kiritilgan qiymat to'g'ri formatda bo'lishi kerak.

**Acceptance Criteria:**
- Vergul (,) yoki nuqta (.) kasr ajratuvchi sifatida qabul qilinadi
- Bo'sh joylar (spaces) raqamlar ichida yoki oxirida olib tashlanadi
- Faqat raqamlar, bitta vergul/nuqta qabul qilinadi
- Noto'g'ri format uchun aniq xato xabari ko'rsatiladi

## 3. Calculator Interfeysi Integratsiyasi

### 3.1 Joriy Kurs Ko'rsatish
Calculator sahifasida joriy dollar kursi ko'rsatilishi kerak.

**Acceptance Criteria:**
- Kurs sahifaning yuqori qismida (rate-bar) ko'rsatiladi
- Format: "Dollar kursi: 12,650.00 so'm"
- Kurs yangilanganda sahifa refresh qilinmasa ham yangi qiymat ko'rsatiladi
- Agar kurs o'rnatilmagan bo'lsa, ogohlantirish ko'rsatiladi

### 3.2 Kurs Yangilash Funksiyasi
Foydalanuvchilar calculator interfeysi orqali kursni yangilashi mumkin bo'lishi kerak.

**Acceptance Criteria:**
- Rate-bar ichida "Yangilash" tugmasi mavjud
- Tugma bosilganda modal/dialog ochiladi
- Dialogda joriy kurs va yangi kurs kiritish maydoni ko'rsatiladi
- Yangi kurs kiritib "Saqlash" bosilganda kurs yangilanadi va tarixga yoziladi
- Bekor qilish (Cancel) imkoniyati mavjud

### 3.3 Kurs Tarixi Ko'rish
Foydalanuvchilar calculator sahifasidan kurs tarixini ko'rishi mumkin.

**Acceptance Criteria:**
- Rate-bar ichida "Tarix" yoki "Ko'proq" havolasi mavjud
- Havola bosilganda kurs tarixi modal/sahifada ko'rsatiladi
- Tarix teskari xronologik tartibda
- Har bir yozuvda: kurs, sana-vaqt, kim o'rnatgan ko'rsatiladi
- Yopish (Close) imkoniyati mavjud

## 4. Buyurtma Hisoblash va Saqlash

### 4.1 Buyurtma Hisoblashda Joriy Kursdan Foydalanish
Yangi buyurtma yaratishda avtomatik joriy kurs ishlatilishi kerak.

**Acceptance Criteria:**
- Yangi quote/order yaratishda joriy kurs avtomatik olinadi
- Kurs BuildQuote.usd_rate maydoniga saqlanadi
- Hisoblash (USD → UZS) joriy kurs bilan bajariladi
- Agar kurs o'rnatilmagan bo'lsa, xato ko'rsatiladi

### 4.2 Buyurtmada Foydalanilgan Kursni Saqlash
Har bir buyurtma o'z kursini saqlab qolishi kerak.

**Acceptance Criteria:**
- BuildQuote.usd_rate buyurtma yaratilgan paytdagi kursni saqlaydi
- Kurs keyinchalik o'zgarganda eski buyurtmalar kursini o'zgartirmaydi
- Buyurtma detalida qaysi kurs ishlatilgani ko'rsatiladi
- Buyurtma yaratilgan sana va kurs tarixiy ravishda mos keladi

## 5. Admin Panel Integratsiyasi

### 5.1 Kurs Tarixi Admin Ko'rinishi
Admin panel orqali kurs tarixini ko'rish va boshqarish mumkin bo'lishi kerak.

**Acceptance Criteria:**
- Django admin da kurs tarixi modeli ro'yxatdan o'tkazilgan
- Ro'yxat ko'rinishida: kurs, sana, foydalanuvchi ko'rsatiladi
- Filtrlash (sana bo'yicha) va qidiruv (kurs bo'yicha) mavjud
- Read-only - tarixiy yozuvlarni o'zgartirish/o'chirish mumkin emas
- Faqat superuser ko'rishi mumkin

### 5.2 CalculatorSettings Admin Yaxshilash
CalculatorSettings admin sahifasida kurs bilan bog'liq ma'lumotlar ko'rsatilishi kerak.

**Acceptance Criteria:**
- Joriy kurs va oxirgi yangilanish sanasi ko'rsatiladi
- Kursni o'zgartirish faqat admin orqali emas, calculator interfeysi orqali ham mumkin
- Admin sahifada "Kurs tarixini ko'rish" havolasi mavjud
- Kurs o'zgarganda avtomatik yangi tarixiy yozuv yaratiladi

## 6. Xavfsizlik va Ruxsatlar

### 6.1 Kurs Yangilash Ruxsati
Faqat vakolatli foydalanuvchilar kursni yangilashi mumkin.

**Acceptance Criteria:**
- Kurs yangilash faqat login qilgan foydalanuvchilarga ruxsat beriladi
- Foydalanuvchi sessiyasi tugasa, kurs yangilash mumkin emas
- Har bir kurs o'zgarishi foydalanuvchi bilan bog'lanadi
- CSRF protection barcha kurs yangilash so'rovlarida mavjud

### 6.2 Kurs Tarixi Ko'rish Ruxsati
Kurs tarixini ko'rish uchun autentifikatsiya talab qilinadi.

**Acceptance Criteria:**
- Kurs tarixi faqat login qilgan foydalanuvchilarga ko'rsatiladi
- Anonim foydalanuvchilar kurs tarixini ko'ra olmaydi
- Tarih sahifasi login_required decorator bilan himoyalangan

## 7. Foydalanuvchi Tajribasi

### 7.1 Kurs Yangilash Feedback
Kurs yangilashda foydalanuvchiga aniq natija ko'rsatilishi kerak.

**Acceptance Criteria:**
- Muvaffaqiyatli yangilanish: "Kurs muvaffaqiyatli yangilandi" xabari
- Xato bo'lsa: aniq xato xabari (masalan: "Kurs juda kichik")
- Loading indicator kurs saqlanayotganda ko'rsatiladi
- Yangilanishdan keyin dialog avtomatik yopiladi

### 7.2 Responsive Dizayn
Barcha kurs boshqaruv elementlari responsive bo'lishi kerak.

**Acceptance Criteria:**
- Kurs yangilash dialogi mobil qurilmalarda to'g'ri ko'rsatiladi
- Kurs tarixi jadvali kichik ekranlarda scroll/adapt qilinadi
- Rate-bar mobil qurilmalarda ham ko'rinadi va foydalanish qulay
- Tugmalar touch-friendly (minimum 44px balandlik)

## 8. Performance va Optimizatsiya

### 8.1 Joriy Kurs Cache
Joriy kurs tez olinishi uchun optimallashtirilishi kerak.

**Acceptance Criteria:**
- Joriy kurs database querylarini minimallashtirish uchun cache qilinadi
- Cache yangilash kurs o'zgarganda avtomatik amalga oshiriladi
- Cache timeout: 1 soat (yoki kurs yangilanguncha)
- get_singleton metodi optimallashtirilgan

### 8.2 Kurs Tarixi Pagination
Katta hajmdagi tarix ma'lumotlari sahifalanishi kerak.

**Acceptance Criteria:**
- Har bir sahifada maksimal 50 ta yozuv
- Pagination kontrollari (keyingi, oldingi, sahifa raqami)
- Jami yozuvlar soni ko'rsatiladi
- Database query optimallashtirilgan (select_related/prefetch_related)

## 9. Ma'lumotlar Migratsiyasi

### 9.1 Mavjud Kursni Tarixga Ko'chirish
Hozirgi CalculatorSettings.usd_rate qiymatini tarixga ko'chirish kerak.

**Acceptance Criteria:**
- Migration yaratiladi va mavjud kurs tarixga ko'chiriladi
- Mavjud kurs uchun tarixiy yozuv yaratiladi
- Yaratilish sanasi migration bajariladigan vaqt
- Foydalanuvchi "system" yoki null bo'lishi mumkin

### 9.2 Backward Compatibility
Yangi model eski funksionallikni buzmaydi.

**Acceptance Criteria:**
- CalculatorSettings.usd_rate hali ham mavjud va ishlatiladi
- Eski quote/order obyektlari yangi tizim bilan to'liq ishlaydi
- Eski API endpointlar (save_usd_rate) yangi tizim bilan integratsiyalangan
- Regresiya testlari o'tkaziladi

## 10. Logging va Monitoring

### 10.1 Kurs O'zgarish Loglari
Har bir kurs o'zgarishi logga yozilishi kerak.

**Acceptance Criteria:**
- Kurs o'zgarishi INFO level log yoziladi
- Log message: eski kurs, yangi kurs, foydalanuvchi, vaqt
- Xato bo'lsa ERROR level log yoziladi
- Log format: structured (JSON yoki key=value)

### 10.2 Monitoring Metrikalar
Kurs bilan bog'liq metrikalar kuzatilishi kerak.

**Acceptance Criteria:**
- Kunlik kurs o'zgarishlar soni
- O'rtacha kurs qiymati (kunlik/haftalik)
- Kurs yangilash xatolar soni
- Metrikalar admin dashboardda yoki monitoring tizimida ko'rinadi
