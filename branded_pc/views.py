import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from calculator.models import CalculatorSettings

from .models import BrandedPc


@login_required
def branded_pc_list(request):
    items = BrandedPc.objects.filter(is_active=True)
    product_data = [
        {"id": i.id, "name": i.name, "price": float(i.price)}
        for i in items
    ]
    settings = CalculatorSettings.get_singleton()
    return render(
        request,
        "branded_pc/branded_pc_list.html",
        {
            "product_data": json.dumps(product_data),
            "usd_rate": float(settings.usd_rate),
            "markup_percent": float(settings.markup_percent),
            "max_discount_percent": settings.max_discount_percent,
            "active_nav": "branded_pc",
            "page_title": "Branded PC",
            "search_placeholder": "Branded PC qidirish...",
        },
    )
