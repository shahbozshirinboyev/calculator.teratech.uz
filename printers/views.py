import json
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from calculator.models import CalculatorSettings

from .models import Printer

SECTION = "printers"


@login_required
def printer_list(request):
    printers = Printer.objects.filter(is_active=True)
    printer_data = [
        {"id": p.id, "name": p.name, "price": float(p.price)}
        for p in printers
    ]
    settings = CalculatorSettings.get_singleton()
    return render(
        request,
        "printers/printer_list.html",
        {
            "product_data": json.dumps(printer_data),
            "usd_rate": float(settings.usd_rate),
            "markup_percent": float(settings.get_markup_for(SECTION)),
            "max_discount_percent": settings.max_discount_percent,
            "active_nav": SECTION,
            "page_title": "Printers",
            "category": "Printer",
            "search_placeholder": "Printer qidirish...",
        },
    )


@login_required
@require_POST
def save_printer_quote(request):
    try:
        printer = Printer.objects.get(pk=request.POST["printer_id"])
    except (Printer.DoesNotExist, KeyError):
        return JsonResponse({"error": "Printer tanlanmadi."}, status=400)

    settings = CalculatorSettings.get_singleton()
    try:
        discount = Decimal(request.POST.get("discount_percent", "0").replace(",", ".").strip())
    except Exception:
        discount = Decimal("0")
    if discount < 0 or discount > settings.max_discount_percent:
        discount = Decimal("0")

    subtotal = printer.price
    total = settings.apply_markup(subtotal, discount, SECTION)

    try:
        usd_rate = Decimal(request.POST.get("usd_rate", "0").replace(",", ".").strip())
    except Exception:
        usd_rate = Decimal("0")
    if usd_rate < 0:
        usd_rate = Decimal("0")
    total_uzs = (total * usd_rate).quantize(Decimal("1")) if usd_rate > 0 else Decimal("0")

    return JsonResponse({
        "name": printer.name,
        "total": f"{total:.2f}",
        "total_uzs": str(total_uzs),
    })
