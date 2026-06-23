import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from calculator.models import CalculatorSettings

from .models import BrandedAio

SECTION = "branded_aio"


@login_required
def branded_aio_list(request):
    items = BrandedAio.objects.filter(is_active=True)
    product_data = [
        {"id": i.id, "name": i.name, "price": float(i.price)}
        for i in items
    ]
    settings = CalculatorSettings.get_singleton()
    return render(
        request,
        "branded_aio/branded_aio_list.html",
        {
            "product_data": json.dumps(product_data),
            "usd_rate": float(settings.usd_rate),
            "markup_percent": float(settings.get_markup_for(SECTION)),
            "max_discount_percent": settings.max_discount_percent,
            "active_nav": SECTION,
            "page_title": "Branded AIO",
            "search_placeholder": "Branded AIO qidirish...",
        },
    )
