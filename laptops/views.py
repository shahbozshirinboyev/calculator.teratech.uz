import json
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from calculator.models import CalculatorSettings

from .models import Laptop


@login_required
def laptop_list(request):
    laptops = Laptop.objects.filter(is_active=True)
    laptop_data = [
        {"id": l.id, "name": l.name, "price": float(l.price)}
        for l in laptops
    ]
    settings = CalculatorSettings.get_singleton()
    return render(
        request,
        "laptops/laptop_list.html",
        {
            "product_data": json.dumps(laptop_data),
            "usd_rate": float(settings.usd_rate),
            "markup_percent": float(settings.markup_percent),
            "max_discount_percent": settings.max_discount_percent,
            "active_nav": "laptops",
            "page_title": "Laptops",
            "search_placeholder": "Laptop qidirish...",
        },
    )


@login_required
@require_POST
def save_laptop_quote(request):
    try:
        laptop = Laptop.objects.get(pk=request.POST["laptop_id"])
    except (Laptop.DoesNotExist, KeyError):
        return JsonResponse({"error": "Laptop tanlanmadi."}, status=400)

    settings = CalculatorSettings.get_singleton()
    try:
        discount = Decimal(
            request.POST.get("discount_percent", "0").replace(",", ".").strip()
        )
    except Exception:
        discount = Decimal("0")
    if discount < 0 or discount > settings.max_discount_percent:
        discount = Decimal("0")

    subtotal = laptop.price
    total = settings.apply_markup(subtotal, discount)

    try:
        usd_rate = Decimal(
            request.POST.get("usd_rate", "0").replace(",", ".").strip()
        )
    except Exception:
        usd_rate = Decimal("0")
    if usd_rate < 0:
        usd_rate = Decimal("0")
    total_uzs = (total * usd_rate).quantize(Decimal("1")) if usd_rate > 0 else Decimal("0")

    return JsonResponse({
        "name": laptop.name,
        "subtotal": f"{subtotal:.2f}",
        "total": f"{total:.2f}",
        "total_uzs": str(total_uzs),
    })
