# Design: Currency Conversion Enhancement

## 1. Overview

Bu design USD dan so'mga o'tkazish tizimini yaxshilash uchun mo'ljallangan. Asosiy maqsad: dollar kursi o'zgarish tarixini saqlash, validatsiya qo'shish va foydalanuvchi interfeysi orqali kursni boshqarish imkoniyatini berish.

### 1.1 Arxitektura Qarori

**Model Layer:**
- `ExchangeRateHistory` - yangi model kurs tarixini saqlash uchun
- `CalculatorSettings` - mavjud model, usd_rate saqlanadi

**View Layer:**
- `update_exchange_rate` - kursni yangilash API endpoint
- `exchange_rate_history` - kurs tarixini ko'rsatish endpoint
- `calculator` - mavjud view, kurs ko'rsatish uchun yangilanadi

**Template Layer:**
- `calculator.html` - kurs yangilash va tarix ko'rish UI qo'shiladi
- Yangi modal dialoglar: kurs yangilash, kurs tarixi

### 1.2 Texnologik Tanlov

- **Framework**: Django ORM (mavjud)
- **Caching**: Django cache framework (optional, performance uchun)
- **Frontend**: Vanilla JavaScript (mavjud arxitekturaga mos)
- **Validation**: Django validators + server-side logic

## 2. Ma'lumotlar Modeli

### 2.1 ExchangeRateHistory Model


**Maqsad**: Har bir dollar kursi o'zgarishini tarixiy yozuv sifatida saqlash.

```python
from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

class ExchangeRateHistory(models.Model):
    """
    Dollar kursi o'zgarish tarixi.
    Har safar kurs yangilanganda yangi yozuv yaratiladi.
    """
    rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Dollar kursi (so'm)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Yaratilgan vaqt"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Kim o'rnatdi"
    )
    
    class Meta:
        db_table = 'calculator_exchange_rate_history'
        ordering = ['-created_at']
        verbose_name = "Kurs tarixi"
        verbose_name_plural = "Kurs tarixi"
        indexes = [
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.rate} so'm - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def get_latest_rate(cls):
        """Eng so'nggi kursni qaytaradi."""
        latest = cls.objects.first()
        return latest.rate if latest else None
    
    @classmethod

    def create_rate(cls, rate, user=None):
        """
        Yangi kurs yaratadi va CalculatorSettings ni yangilaydi.
        
        Args:
            rate: Decimal - yangi kurs qiymati
            user: User - kim o'rnatdi
            
        Returns:
            ExchangeRateHistory instance
            
        Raises:
            ValidationError - agar rate noto'g'ri bo'lsa
        """
        from django.core.exceptions import ValidationError
        
        # Validatsiya
        if rate <= Decimal('100'):
            raise ValidationError("Kurs 100 dan katta bo'lishi kerak.")
        if rate >= Decimal('1000000'):
            raise ValidationError("Kurs 1,000,000 dan kichik bo'lishi kerak.")
        
        # Yangi tarixiy yozuv yaratish
        history_entry = cls.objects.create(
            rate=rate,
            created_by=user
        )
        
        # CalculatorSettings ni yangilash
        from calculator.models import CalculatorSettings
        settings = CalculatorSettings.get_singleton()
        settings.usd_rate = rate
        settings.save(update_fields=['usd_rate', 'updated_at'])
        
        return history_entry
```

**Requirements Coverage:**
- 1.1: Har bir kurs o'zgarishi alohida yozuv
- 1.2: get_latest_rate() eng so'nggi kursni qaytaradi
- 2.1: Validatsiya create_rate() ichida
- 6.1: created_by maydoni autentifikatsiya uchun



### 2.2 CalculatorSettings Model O'zgarishlari

**Maqsad**: Mavjud model bilan integratsiya, backward compatibility.

```python
# calculator/models.py ga qo'shimcha

class CalculatorSettings(models.Model):
    # ... mavjud fieldlar ...
    
    @classmethod
    def sync_rate_from_history(cls):
        """
        ExchangeRateHistory dan eng so'nggi kursni oladi va 
        CalculatorSettings ni yangilaydi.
        Migration va recovery uchun foydali.
        """
        from calculator.models import ExchangeRateHistory
        latest_rate = ExchangeRateHistory.get_latest_rate()
        
        if latest_rate:
            settings = cls.get_singleton()
            settings.usd_rate = latest_rate
            settings.save(update_fields=['usd_rate', 'updated_at'])
            return True
        return False
```

**Requirements Coverage:**
- 1.2: Joriy kurs olish
- 9.2: Backward compatibility

## 3. View Functions

### 3.1 Kurs Yangilash View

**Maqsad**: AJAX orqali yangi kurs qabul qilish va saqlash.

```python
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation
import logging

logger = logging.getLogger(__name__)

@login_required
@require_POST
def update_exchange_rate(request):

    """
    Yangi dollar kursini qabul qiladi va tarixga saqlaydi.
    
    POST parameters:
        new_rate (str): Yangi kurs qiymati
        
    Returns:
        JSON: {success: bool, rate: str, message: str}
    """
    try:
        # Input olish va tozalash
        raw_rate = request.POST.get('new_rate', '').strip()
        raw_rate = raw_rate.replace(',', '.').replace(' ', '')
        
        # Decimal ga o'tkazish
        try:
            new_rate = Decimal(raw_rate)
        except InvalidOperation:
            return JsonResponse({
                'success': False,
                'message': 'Kurs noto\'g\'ri formatda. Faqat raqam kiriting.'
            }, status=400)
        
        # Yangi kurs yaratish (validatsiya ichida)
        from calculator.models import ExchangeRateHistory
        history = ExchangeRateHistory.create_rate(
            rate=new_rate,
            user=request.user
        )
        
        # Muvaffaqiyatli log
        logger.info(
            f"Exchange rate updated: {new_rate} by {request.user.username}",
            extra={
                'old_rate': ExchangeRateHistory.objects.filter(
                    created_at__lt=history.created_at
                ).first().rate if ExchangeRateHistory.objects.count() > 1 else None,
                'new_rate': new_rate,
                'user': request.user.username
            }
        )
        
        return JsonResponse({
            'success': True,
            'rate': f"{history.rate:,.2f}",
            'message': 'Kurs muvaffaqiyatli yangilandi!'
        })
        
    except ValidationError as e:

        logger.error(f"Exchange rate validation error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)
        
    except Exception as e:
        logger.error(f"Exchange rate update error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Xatolik yuz berdi. Iltimos qaytadan urinib ko\'ring.'
        }, status=500)
```

**Requirements Coverage:**
- 2.1, 2.2: Validatsiya va format tekshiruvi
- 3.2: Kurs yangilash funksiyasi
- 6.1: login_required decorator
- 7.1: Feedback messages
- 10.1: Logging

### 3.2 Kurs Tarixi Ko'rish View

```python
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render

@login_required
def exchange_rate_history(request):
    """
    Kurs o'zgarish tarixini ko'rsatadi (pagination bilan).
    
    GET parameters:
        page (int): Sahifa raqami (default: 1)
        
    Returns:
        Rendered template with paginated history
    """
    from calculator.models import ExchangeRateHistory
    
    # Barcha tarixni olish
    history_list = ExchangeRateHistory.objects.select_related('created_by').all()
    
    # Pagination

    paginator = Paginator(history_list, 50)  # 50 per page
    page_number = request.GET.get('page', 1)
    
    try:
        history_page = paginator.page(page_number)
    except PageNotAnInteger:
        history_page = paginator.page(1)
    except EmptyPage:
        history_page = paginator.page(paginator.num_pages)
    
    context = {
        'history': history_page,
        'total_count': paginator.count
    }
    
    return render(request, 'calculator/exchange_rate_history.html', context)
```

**Requirements Coverage:**
- 1.3: Kurs tarixi ko'rsatish
- 6.2: login_required decorator
- 8.2: Pagination

### 3.3 Calculator View Yangilanishi

```python
@login_required
def calculator(request):
    # ... mavjud kod ...
    
    # Joriy kursni olish
    from calculator.models import ExchangeRateHistory
    latest_rate_history = ExchangeRateHistory.objects.first()
    
    settings = CalculatorSettings.get_singleton()
    
    # Agar kurs o'rnatilmagan bo'lsa, ogohlantirish
    rate_warning = None
    if not settings.usd_rate or settings.usd_rate <= 0:
        rate_warning = "Diqqat: Dollar kursi o'rnatilmagan!"
    
    context = {
        # ... mavjud context ...
        'usd_rate': float(settings.usd_rate) if settings.usd_rate else 0,
        'rate_warning': rate_warning,
        'last_rate_update': latest_rate_history.created_at if latest_rate_history else None,
    }
    
    return render(request, 'calculator/calculator.html', context)
```

**Requirements Coverage:**
- 3.1: Joriy kurs ko'rsatish



## 4. URL Configuration

```python
# calculator/urls.py

from django.urls import path
from . import views

app_name = 'calculator'

urlpatterns = [
    # ... mavjud URLlar ...
    path('calculator/', views.calculator, name='calculator'),
    
    # Yangi URLlar
    path('api/update-exchange-rate/', views.update_exchange_rate, name='update_exchange_rate'),
    path('exchange-rate-history/', views.exchange_rate_history, name='exchange_rate_history'),
]
```

**Requirements Coverage:**
- 3.2, 3.3: API endpoints

## 5. Frontend Implementation

### 5.1 Calculator Template Yangilanishi

**Maqsad**: Rate-bar ni ko'rsatish, kurs yangilash va tarix ko'rish UI qo'shish.

```html
<!-- calculator/templates/calculator/calculator.html -->

{% block extra_css %}
/* ... mavjud CSS ... */

/* Rate bar CSS - ko'rinadigan qilish */
.rate-bar {
  display: flex !important; /* Override existing display: none */
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 8px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.rate-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rate-label {
  font-size: 14px;
  opacity: 0.9;
}

.rate-value {
  font-size: 20px;
  font-weight: 700;
}

.rate-actions {
  display: flex;
  gap: 8px;
}



.rate-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s;
}

.rate-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.rate-warning {
  background: #fef3c7;
  border: 1px solid #fbbf24;
  color: #92400e;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;
}

/* Modal styles */
.modal-overlay {
  display: none;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 9999;
  align-items: center;
  justify-content: center;
}

.modal-overlay.active {
  display: flex;
}

.modal-content {
  background: var(--panel);
  border-radius: 12px;
  padding: 24px;
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.modal-title {
  font-size: 18px;
  font-weight: 700;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--muted);
}



.modal-body {
  margin-bottom: 20px;
}

.modal-footer {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

@media (max-width: 640px) {
  .rate-bar {
    flex-direction: column;
    gap: 12px;
  }
  
  .rate-actions {
    width: 100%;
    justify-content: stretch;
  }
  
  .rate-btn {
    flex: 1;
  }
}

{% endblock %}

{% block content %}
<!-- Rate bar -->
<div class="rate-bar">
  <div class="rate-info">
    <span class="rate-label">Dollar kursi:</span>
    <span class="rate-value" id="current-rate">{{ usd_rate|floatformat:2 }} so'm</span>
    {% if last_rate_update %}
    <span style="font-size: 12px; opacity: 0.8;">
      ({{ last_rate_update|date:"d.m.Y H:i" }})
    </span>
    {% endif %}
  </div>
  <div class="rate-actions">
    <button class="rate-btn" onclick="openUpdateRateModal()">
      <span>✏️</span> Yangilash
    </button>
    <button class="rate-btn" onclick="openRateHistoryModal()">
      <span>📊</span> Tarix
    </button>
  </div>
</div>

{% if rate_warning %}
<div class="rate-warning">
  ⚠️ {{ rate_warning }}
</div>
{% endif %}

<!-- ... mavjud calculator content ... -->

<!-- Kurs yangilash modali -->
<div class="modal-overlay" id="update-rate-modal">
  <div class="modal-content">
    <div class="modal-header">
      <h3 class="modal-title">Dollar kursini yangilash</h3>
      <button class="modal-close" onclick="closeUpdateRateModal()">&times;</button>
    </div>

    <div class="modal-body">
      <div class="field" style="margin-bottom: 16px;">
        <label>Joriy kurs</label>
        <input type="text" value="{{ usd_rate|floatformat:2 }} so'm" readonly 
               style="background: var(--bg); cursor: not-allowed;">
      </div>
      <div class="field">
        <label>Yangi kurs (so'm) *</label>
        <input type="number" id="new-rate-input" placeholder="12650.00" 
               step="0.01" min="100" max="999999" required
               style="font-size: 16px; font-weight: 600;">
      </div>
      <div id="rate-error" style="color: var(--danger); font-size: 13px; margin-top: 8px; display: none;"></div>
      <div id="rate-success" style="color: var(--success); font-size: 13px; margin-top: 8px; display: none;"></div>
    </div>
    <div class="modal-footer">
      <button type="button" onclick="closeUpdateRateModal()"
              style="background: var(--btn-secondary-bg); color: var(--btn-secondary-color); 
                     border: 1px solid var(--btn-secondary-border);">
        Bekor qilish
      </button>
      <button type="button" id="save-rate-btn" onclick="saveNewRate()"
              style="background: var(--accent); color: white; border: none;">
        <span id="save-rate-text">Saqlash</span>
        <span id="save-rate-loading" style="display: none;">⏳ Saqlanmoqda...</span>
      </button>
    </div>
  </div>
</div>

<!-- Kurs tarixi modali -->
<div class="modal-overlay" id="rate-history-modal">
  <div class="modal-content" style="max-width: 700px;">
    <div class="modal-header">
      <h3 class="modal-title">Kurs o'zgarish tarixi</h3>
      <button class="modal-close" onclick="closeRateHistoryModal()">&times;</button>
    </div>
    <div class="modal-body" id="history-content">
      <p style="text-align: center; color: var(--muted);">Yuklanmoqda...</p>
    </div>
  </div>
</div>

{% endblock %}
```

**Requirements Coverage:**
- 3.1: Joriy kurs ko'rsatish
- 3.2: Kurs yangilash UI
- 3.3: Kurs tarixi ko'rish UI
- 7.2: Responsive dizayn



### 5.2 JavaScript Funksiyalar

```javascript
// calculator.html ichida {% block extra_js %}

// Modal ochish/yopish
function openUpdateRateModal() {
  document.getElementById('update-rate-modal').classList.add('active');
  document.getElementById('new-rate-input').focus();
}

function closeUpdateRateModal() {
  document.getElementById('update-rate-modal').classList.remove('active');
  document.getElementById('new-rate-input').value = '';
  document.getElementById('rate-error').style.display = 'none';
  document.getElementById('rate-success').style.display = 'none';
}

function openRateHistoryModal() {
  const modal = document.getElementById('rate-history-modal');
  modal.classList.add('active');
  loadRateHistory();
}

function closeRateHistoryModal() {
  document.getElementById('rate-history-modal').classList.remove('active');
}

// Yangi kurs saqlash
async function saveNewRate() {
  const newRateInput = document.getElementById('new-rate-input');
  const newRate = newRateInput.value.trim();
  
  // Validatsiya
  if (!newRate) {
    showRateError('Iltimos, yangi kurs qiymatini kiriting.');
    return;
  }
  
  const rateNum = parseFloat(newRate);
  if (isNaN(rateNum) || rateNum <= 100 || rateNum >= 1000000) {
    showRateError('Kurs 100 dan katta va 1,000,000 dan kichik bo\'lishi kerak.');
    return;
  }
  
  // Loading state
  const saveBtn = document.getElementById('save-rate-btn');
  saveBtn.disabled = true;
  document.getElementById('save-rate-text').style.display = 'none';
  document.getElementById('save-rate-loading').style.display = 'inline';
  
  try {
    // CSRF token olish
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
    // API ga so'rov

    const response = await fetch('/api/update-exchange-rate/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: `new_rate=${encodeURIComponent(newRate)}`
    });
    
    const data = await response.json();
    
    if (data.success) {
      // Muvaffaqiyatli
      showRateSuccess(data.message);
      
      // UI yangilash
      document.getElementById('current-rate').textContent = data.rate + ' so\'m';
      
      // 1.5 soniya kutib modal yopish
      setTimeout(() => {
        closeUpdateRateModal();
        location.reload(); // Sahifani yangilash
      }, 1500);
    } else {
      showRateError(data.message);
    }
  } catch (error) {
    console.error('Error updating rate:', error);
    showRateError('Xatolik yuz berdi. Iltimos qaytadan urinib ko\'ring.');
  } finally {
    // Loading state qaytarish
    saveBtn.disabled = false;
    document.getElementById('save-rate-text').style.display = 'inline';
    document.getElementById('save-rate-loading').style.display = 'none';
  }
}

function showRateError(message) {
  const errorEl = document.getElementById('rate-error');
  errorEl.textContent = message;
  errorEl.style.display = 'block';
  document.getElementById('rate-success').style.display = 'none';
}

function showRateSuccess(message) {
  const successEl = document.getElementById('rate-success');
  successEl.textContent = message;
  successEl.style.display = 'block';
  document.getElementById('rate-error').style.display = 'none';
}

// Kurs tarixini yuklash
async function loadRateHistory() {
  const contentEl = document.getElementById('history-content');
  contentEl.innerHTML = '<p style="text-align: center; color: var(--muted);">Yuklanmoqda...</p>';
  
  try {

    const response = await fetch('/exchange-rate-history/');
    const html = await response.text();
    
    // Parse HTML and extract history content
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const historyTable = doc.querySelector('.history-table');
    
    if (historyTable) {
      contentEl.innerHTML = historyTable.outerHTML;
    } else {
      contentEl.innerHTML = '<p style="text-align: center; color: var(--muted);">Tarix mavjud emas.</p>';
    }
  } catch (error) {
    console.error('Error loading history:', error);
    contentEl.innerHTML = '<p style="text-align: center; color: var(--danger);">Xatolik yuz berdi.</p>';
  }
}

// Modal tashqarisiga bosilganda yopish
document.getElementById('update-rate-modal').addEventListener('click', (e) => {
  if (e.target.id === 'update-rate-modal') {
    closeUpdateRateModal();
  }
});

document.getElementById('rate-history-modal').addEventListener('click', (e) => {
  if (e.target.id === 'rate-history-modal') {
    closeRateHistoryModal();
  }
});

// Enter tugmasi bosilganda saqlash
document.getElementById('new-rate-input')?.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    saveNewRate();
  }
});
```

**Requirements Coverage:**
- 3.2: Kurs yangilash funksiyasi
- 3.3: Kurs tarixi yuklash
- 7.1: Feedback va loading states
- 7.2: Responsive (modal yopish)



### 5.3 Kurs Tarixi Template

```html
<!-- calculator/templates/calculator/exchange_rate_history.html -->

{% extends "base.html" %}

{% block title %}Kurs tarixi{% endblock %}

{% block content %}
<div style="max-width: 900px; margin: 20px auto;">
  <h2 style="margin-bottom: 20px;">Kurs o'zgarish tarixi</h2>
  
  <div class="panel history-table" style="overflow-x: auto;">
    {% if history %}
    <table style="width: 100%; border-collapse: collapse;">
      <thead>
        <tr style="border-bottom: 2px solid var(--line);">
          <th style="padding: 12px; text-align: left; font-weight: 700;">Kurs (so'm)</th>
          <th style="padding: 12px; text-align: left; font-weight: 700;">Sana va vaqt</th>
          <th style="padding: 12px; text-align: left; font-weight: 700;">Kim o'rnatdi</th>
        </tr>
      </thead>
      <tbody>
        {% for entry in history %}
        <tr style="border-bottom: 1px solid var(--line);">
          <td style="padding: 12px; font-weight: 600; color: var(--accent);">
            {{ entry.rate|floatformat:2 }}
          </td>
          <td style="padding: 12px; color: var(--text);">
            {{ entry.created_at|date:"d.m.Y H:i" }}
          </td>
          <td style="padding: 12px; color: var(--muted);">
            {% if entry.created_by %}
              {{ entry.created_by.username }}
            {% else %}
              System
            {% endif %}
          </td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
    
    <!-- Pagination -->
    {% if history.has_other_pages %}
    <div style="display: flex; justify-content: center; align-items: center; 
                gap: 10px; margin-top: 20px; padding: 16px;">
      {% if history.has_previous %}
        <a href="?page=1" class="rate-btn">Birinchi</a>
        <a href="?page={{ history.previous_page_number }}" class="rate-btn">Oldingi</a>
      {% endif %}
      
      <span style="color: var(--muted); font-size: 14px;">
        Sahifa {{ history.number }} / {{ history.paginator.num_pages }}
      </span>
      
      {% if history.has_next %}
        <a href="?page={{ history.next_page_number }}" class="rate-btn">Keyingi</a>
        <a href="?page={{ history.paginator.num_pages }}" class="rate-btn">Oxirgi</a>
      {% endif %}
    </div>
    {% endif %}
    
    <p style="text-align: center; color: var(--muted); font-size: 13px; margin-top: 16px;">
      Jami: {{ total_count }} ta yozuv
    </p>
    {% else %}
    <p style="text-align: center; color: var(--muted); padding: 40px;">
      Hozircha tarix mavjud emas.
    </p>
    {% endif %}
  </div>
  
  <div style="margin-top: 20px;">
    <a href="{% url 'calculator:calculator' %}" class="rate-btn">
      ← Calculatorga qaytish
    </a>
  </div>
</div>
{% endblock %}
```

**Requirements Coverage:**
- 1.3: Kurs tarixi ko'rsatish
- 8.2: Pagination



## 6. Django Admin Integration

### 6.1 ExchangeRateHistory Admin

```python
# calculator/admin.py

from django.contrib import admin
from .models import ExchangeRateHistory

@admin.register(ExchangeRateHistory)
class ExchangeRateHistoryAdmin(admin.ModelAdmin):
    """
    Admin interfeys kurs tarixi uchun.
    Read-only - faqat ko'rish mumkin.
    """
    list_display = ('rate', 'created_at', 'created_by')
    list_filter = ('created_at',)
    search_fields = ('rate',)
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    # Read-only qilish
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
    
    # Faqat superuser ko'rishi mumkin
    def has_module_permission(self, request):
        return request.user.is_superuser
```

**Requirements Coverage:**
- 5.1: Admin panel integratsiya

## 7. Database Migration

### 7.1 Initial Migration

```python
# calculator/migrations/0014_exchangeratehistory.py

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('calculator', '0013_add_per_section_markup'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExchangeRateHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rate', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Dollar kursi (so'm)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan vaqt')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Kim o\'rnatdi')),
            ],
            options={
                'verbose_name': 'Kurs tarixi',
                'verbose_name_plural': 'Kurs tarixi',
                'db_table': 'calculator_exchange_rate_history',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='exchangeratehistory',
            index=models.Index(fields=['-created_at'], name='calculator_e_created_idx'),
        ),
    ]
```



### 7.2 Data Migration - Mavjud Kursni Tarixga Ko'chirish

```python
# calculator/migrations/0015_migrate_existing_rate.py

from django.db import migrations
from decimal import Decimal


def migrate_existing_rate(apps, schema_editor):
    """
    Mavjud CalculatorSettings.usd_rate ni ExchangeRateHistory ga ko'chirish.
    """
    CalculatorSettings = apps.get_model('calculator', 'CalculatorSettings')
    ExchangeRateHistory = apps.get_model('calculator', 'ExchangeRateHistory')
    
    try:
        settings = CalculatorSettings.objects.get(pk=1)
        if settings.usd_rate and settings.usd_rate > Decimal('0'):
            # Tarixiy yozuv yaratish
            ExchangeRateHistory.objects.create(
                rate=settings.usd_rate,
                created_by=None  # System migration
            )
            print(f"Migrated existing rate: {settings.usd_rate}")
    except CalculatorSettings.DoesNotExist:
        print("No existing CalculatorSettings found, skipping migration.")


def reverse_migration(apps, schema_editor):
    """
    Rollback - birinchi tarixiy yozuvni o'chirish.
    """
    ExchangeRateHistory = apps.get_model('calculator', 'ExchangeRateHistory')
    ExchangeRateHistory.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('calculator', '0014_exchangeratehistory'),
    ]

    operations = [
        migrations.RunPython(migrate_existing_rate, reverse_migration),
    ]
```

**Requirements Coverage:**
- 9.1: Mavjud kursni tarixga ko'chirish
- 9.2: Backward compatibility



## 8. Testing Strategy

### 8.1 Unit Tests

```python
# calculator/tests/test_exchange_rate.py

from django.test import TestCase
from django.contrib.auth.models import User
from decimal import Decimal
from calculator.models import ExchangeRateHistory, CalculatorSettings

class ExchangeRateHistoryTestCase(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_create_rate_valid(self):
        """Valid kurs yaratish."""
        rate = Decimal('12650.50')
        history = ExchangeRateHistory.create_rate(rate, self.user)
        
        self.assertEqual(history.rate, rate)
        self.assertEqual(history.created_by, self.user)
        
        # CalculatorSettings yangilangan bo'lishi kerak
        settings = CalculatorSettings.get_singleton()
        self.assertEqual(settings.usd_rate, rate)
    
    def test_create_rate_too_low(self):
        """Juda kichik kurs xato berishi kerak."""
        from django.core.exceptions import ValidationError
        
        with self.assertRaises(ValidationError):
            ExchangeRateHistory.create_rate(Decimal('50'), self.user)
    
    def test_create_rate_too_high(self):
        """Juda katta kurs xato berishi kerak."""
        from django.core.exceptions import ValidationError
        
        with self.assertRaises(ValidationError):
            ExchangeRateHistory.create_rate(Decimal('2000000'), self.user)
    
    def test_get_latest_rate(self):
        """Eng so'nggi kursni olish."""
        ExchangeRateHistory.create_rate(Decimal('12000'), self.user)
        ExchangeRateHistory.create_rate(Decimal('12500'), self.user)
        latest = ExchangeRateHistory.create_rate(Decimal('13000'), self.user)
        
        retrieved = ExchangeRateHistory.get_latest_rate()
        self.assertEqual(retrieved, latest.rate)
```



### 8.2 View Tests

```python
# calculator/tests/test_views.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from decimal import Decimal
from calculator.models import ExchangeRateHistory

class UpdateExchangeRateViewTestCase(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        self.url = reverse('calculator:update_exchange_rate')
    
    def test_update_rate_success(self):
        """Kurs muvaffaqiyatli yangilanishi."""
        response = self.client.post(self.url, {
            'new_rate': '12650.00'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['rate'], '12,650.00')
    
    def test_update_rate_invalid_format(self):
        """Noto'g'ri format xato berishi kerak."""
        response = self.client.post(self.url, {
            'new_rate': 'abc'
        })
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
    
    def test_update_rate_unauthorized(self):
        """Login qilmagan foydalanuvchi ruxsat olmaydi."""
        self.client.logout()
        response = self.client.post(self.url, {
            'new_rate': '12650.00'
        })
        
        self.assertEqual(response.status_code, 302)  # Redirect to login
```

**Requirements Coverage:**
- Barcha asosiy funksiyalar test qilinadi
- Unit tests va integration tests



## 9. Performance Optimizations

### 9.1 Caching Strategy

```python
# calculator/models.py ichida

from django.core.cache import cache

class ExchangeRateHistory(models.Model):
    # ... mavjud kod ...
    
    CACHE_KEY = 'latest_exchange_rate'
    CACHE_TIMEOUT = 3600  # 1 soat
    
    @classmethod
    def get_latest_rate_cached(cls):
        """
        Eng so'nggi kursni cache dan oladi.
        Cache bo'sh bo'lsa, database dan oladi va cache ga saqlaydi.
        """
        cached_rate = cache.get(cls.CACHE_KEY)
        
        if cached_rate is not None:
            return cached_rate
        
        # Cache bo'sh, database dan olish
        latest = cls.objects.first()
        rate = latest.rate if latest else None
        
        if rate:
            cache.set(cls.CACHE_KEY, rate, cls.CACHE_TIMEOUT)
        
        return rate
    
    @classmethod
    def create_rate(cls, rate, user=None):
        # ... mavjud validatsiya ...
        
        history_entry = cls.objects.create(rate=rate, created_by=user)
        
        # CalculatorSettings yangilash
        from calculator.models import CalculatorSettings
        settings = CalculatorSettings.get_singleton()
        settings.usd_rate = rate
        settings.save(update_fields=['usd_rate', 'updated_at'])
        
        # Cache yangilash
        cache.set(cls.CACHE_KEY, rate, cls.CACHE_TIMEOUT)
        
        return history_entry
```

**Requirements Coverage:**
- 8.1: Joriy kurs cache

### 9.2 Database Query Optimization

```python
# calculator/views.py ichida

@login_required
def exchange_rate_history(request):
    # select_related ishlatish - N+1 query muammosini oldini olish
    history_list = ExchangeRateHistory.objects.select_related(
        'created_by'
    ).all()
    
    # ... pagination ...
```

**Requirements Coverage:**
- 8.2: Query optimizatsiya



## 10. Error Handling and Logging

### 10.1 Logging Configuration

```python
# config/settings.py ichida

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'exchange_rate.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'calculator.views': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

**Requirements Coverage:**
- 10.1: Kurs o'zgarish loglari

## 11. Security Considerations

### 11.1 CSRF Protection

Barcha POST requestlarda CSRF token ishlatiladi:

```javascript
// JavaScript da
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
```

### 11.2 Input Validation

- Server-side validatsiya (Django)
- Client-side validatsiya (JavaScript)
- SQL injection oldini olish (Django ORM)

### 11.3 Authentication

- `@login_required` decorator barcha view larda
- Session-based authentication

**Requirements Coverage:**
- 6.1, 6.2: Xavfsizlik va ruxsatlar

## 12. Deployment Checklist

### 12.1 Pre-deployment

- [ ] Barcha migratsiyalar yaratilgan
- [ ] Testlar o'tkazilgan va muvaffaqiyatli
- [ ] Static fayllar yig'ilgan (`collectstatic`)
- [ ] Logging sozlangan

### 12.2 Deployment

- [ ] Database backup olingan
- [ ] Migratsiyalar bajarilgan: `python manage.py migrate`
- [ ] Mavjud kurs tarixga ko'chirilgan
- [ ] Server qayta ishga tushirilgan

### 12.3 Post-deployment

- [ ] Kurs yangilash funksiyasi test qilingan
- [ ] Kurs tarixi to'g'ri ko'rsatiladi
- [ ] Loglar tekshirilgan



## 13. Correctness Properties

Bu bo'limda design da aniqlangan funksiyalar uchun to'g'rilik xossalari keltirilgan.

### Property 1: Kurs Tarixi Yaxlitligi (History Integrity)
**Validates Requirements:** 1.1, 1.2

**Property:**
Har bir kurs o'zgarishi tarixda saqlanadi va eng so'nggi kurs har doim joriy kurs bilan mos keladi.

**Formal Definition:**
```
∀ time t: 
  latest_rate_at(t) = CalculatorSettings.usd_rate_at(t)
  AND
  ∀ history_entry h where h.created_at <= t:
    h exists in ExchangeRateHistory
```

**Test Strategy:**
- Create multiple rate changes
- Verify each change creates a history entry
- Verify latest history rate matches CalculatorSettings.usd_rate

### Property 2: Kurs Validatsiya Monotonicity
**Validates Requirements:** 2.1

**Property:**
Kurs qiymati har doim belgilangan diapazon ichida bo'lishi kerak.

**Formal Definition:**
```
∀ rate r in ExchangeRateHistory:
  100 < r < 1,000,000
  AND
  r.decimal_places <= 2
```

**Test Strategy:**
- Attempt to create rate with value <= 100 (should fail)
- Attempt to create rate with value >= 1,000,000 (should fail)
- Verify decimal precision is enforced

### Property 3: Authentication Invariant
**Validates Requirements:** 6.1, 6.2

**Property:**
Kurs operatsiyalari faqat autentifikatsiya qilingan foydalanuvchilar tomonidan amalga oshiriladi.

**Formal Definition:**
```
∀ operation op in {create_rate, view_history}:
  op.allowed ⟺ user.is_authenticated = True
```

**Test Strategy:**
- Attempt rate update without login (should redirect/fail)
- Attempt history view without login (should redirect/fail)
- Verify authenticated user can perform operations

### Property 4: Cache Consistency
**Validates Requirements:** 8.1

**Property:**
Cache da saqlanayotgan kurs har doim database dagi eng so'nggi kurs bilan mos keladi.

**Formal Definition:**
```
∀ time t after cache_refresh:
  cached_rate = ExchangeRateHistory.get_latest_rate()
  AND
  cached_rate = CalculatorSettings.usd_rate
```

**Test Strategy:**
- Create new rate
- Verify cache is updated immediately
- Verify cached value matches database value

### Property 5: Tarixiy Yozuvlarning O'zgarmasligi (Immutability)
**Validates Requirements:** 1.1, 5.1

**Property:**
Bir marta yaratilgan tarixiy yozuvlar o'zgartirilmaydi va o'chirilmaydi.

**Formal Definition:**
```
∀ history_entry h:
  h.created_at is immutable
  AND
  h.rate is immutable
  AND
  h.created_by is immutable
  AND
  delete(h) is not allowed
```

**Test Strategy:**
- Verify admin interface disallows edit/delete
- Verify model-level protections
- Verify history entries persist across rate updates

