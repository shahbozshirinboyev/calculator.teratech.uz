import json
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from calculator.models import CalculatorSettings

from .models import Monitor

SECTION = "monitors"


@login_required
def monitor_list(request):
    monitors = Monitor.objects.filter(is_active=True)
    monitor_data = [
        {"id": m.id, "name": m.name, "price": float(m.price)}
        for m in monitors
    ]
    settings = CalculatorSettings.get_singleton()
    return render(
        request,
        "monitors/monitor_list.html",
        {
            "product_data": json.dumps(monitor_data),
            "usd_rate": float(settings.usd_rate),
            "markup_percent": float(settings.get_markup_for(SECTION)),
            "max_discount_percent": settings.max_discount_percent,
            "active_nav": SECTION,
            "page_title": "Monitors",
            "category": "Monitor",
            "search_placeholder": "Monitor qidirish...",
        },
    )


@login_required
@require_POST
def save_monitor_quote(request):
    try:
        monitor = Monitor.objects.get(pk=request.POST["monitor_id"])
    except (Monitor.DoesNotExist, KeyError):
        return JsonResponse({"error": "Monitor tanlanmadi."}, status=400)

    settings = CalculatorSettings.get_singleton()
    try:
        discount = Decimal(request.POST.get("discount_percent", "0").replace(",", ".").strip())
    except Exception:
        discount = Decimal("0")
    if discount < 0 or discount > settings.max_discount_percent:
        discount = Decimal("0")

    subtotal = monitor.price
    total = settings.apply_markup(subtotal, discount, SECTION)

    try:
        usd_rate = Decimal(request.POST.get("usd_rate", "0").replace(",", ".").strip())
    except Exception:
        usd_rate = Decimal("0")
    if usd_rate < 0:
        usd_rate = Decimal("0")
    total_uzs = (total * usd_rate).quantize(Decimal("1")) if usd_rate > 0 else Decimal("0")

    return JsonResponse({
        "name": monitor.name,
        "total": f"{total:.2f}",
        "total_uzs": str(total_uzs),
    })
