from decimal import Decimal
import json

from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Max
from django.views.decorators.http import require_POST

from products.models import CPU, RAM, KeyboardMouse, MonoblockBase, Storage

from .models import BuildQuote, CalculatorSettings


def calculator(request):
    bases = MonoblockBase.objects.filter(is_active=True)
    base_data = [
        {
            "id": item.id,
            "name": str(item),
            "motherboard_type": item.motherboard_type,
            "ram_type": item.ram_type,
            "ram_type_label": item.get_ram_type_display(),
            "ram_slots": item.ram_slots,
            "supports_sata": item.supports_sata,
            "supports_nvme": item.supports_nvme,
            "price": float(item.price),
        }
        for item in bases
    ]
    cpu_data = [
        {
            "id": item.id,
            "name": item.name,
            "price": float(item.price),
            "bases": list(item.compatible_bases.values_list("id", flat=True)),
        }
        for item in CPU.objects.filter(is_active=True).prefetch_related("compatible_bases")
    ]
    ram_data = [
        {"id": item.id, "name": item.name, "price": float(item.price), "ram_type": item.ram_type, "capacity_gb": item.capacity_gb}
        for item in RAM.objects.filter(is_active=True)
    ]
    storage_data = [
        {
            "id": item.id,
            "name": item.name,
            "price": float(item.price),
            "kind": item.kind,
            "interface": item.interface,
            "capacity_gb": item.capacity_gb,
        }
        for item in Storage.objects.filter(is_active=True)
    ]
    keyboard_mouse_data = [
        {"id": item.id, "name": item.name, "price": float(item.price)}
        for item in KeyboardMouse.objects.filter(is_active=True)
    ]
    settings = CalculatorSettings.get_singleton()
    next_quote_id = (BuildQuote.objects.aggregate(max_id=Max("id"))["max_id"] or 0) + 1
    return render(
        request,
        "calculator/calculator.html",
        {
            "base_data": json.dumps(base_data),
            "cpu_data": json.dumps(cpu_data),
            "ram_data": json.dumps(ram_data),
            "storage_data": json.dumps(storage_data),
            "keyboard_mouse_data": json.dumps(keyboard_mouse_data),
            "usd_rate": float(settings.usd_rate),
            "next_order_number": f"AIO#{next_quote_id}",
        },
    )


@require_POST
def save_usd_rate(request):
    try:
        rate = Decimal(request.POST.get("usd_rate", "0").replace(",", ".").strip())
    except Exception:
        return JsonResponse({"error": "Kurs noto'g'ri kiritildi."}, status=400)
    if rate <= 0:
        return JsonResponse({"error": "Kurs 0 dan katta bo'lishi kerak."}, status=400)
    settings = CalculatorSettings.get_singleton()
    settings.usd_rate = rate
    settings.save(update_fields=["usd_rate", "updated_at"])
    return JsonResponse({"usd_rate": f"{settings.usd_rate:.2f}"})


@require_POST
def save_quote(request):
    monoblock_base = MonoblockBase.objects.get(pk=request.POST["monoblock_base"])
    cpu = CPU.objects.get(pk=request.POST["cpu"])
    keyboard_mouse = None
    ram_ids = [value for value in request.POST.getlist("ram_slots") if value]
    if request.POST.get("ram"):
        ram_ids.append(request.POST["ram"])
    storage_ids = [value for value in request.POST.getlist("storage_slots") if value]
    ram_map = RAM.objects.in_bulk(ram_ids)
    storage_map = Storage.objects.in_bulk(storage_ids)
    rams = [ram_map[int(pk)] for pk in ram_ids if int(pk) in ram_map]
    storages = [storage_map[int(pk)] for pk in storage_ids if int(pk) in storage_map]

    if request.POST.get("keyboard_mouse"):
        keyboard_mouse = KeyboardMouse.objects.get(pk=request.POST["keyboard_mouse"])

    ram_items = [{"id": item.id, "name": item.name, "price": str(item.price)} for item in rams]
    storage_items = [{"id": item.id, "name": item.name, "price": str(item.price)} for item in storages]
    subtotal = (
        monoblock_base.price
        + cpu.price
        + sum((item.price for item in rams), Decimal("0"))
        + sum((item.price for item in storages), Decimal("0"))
        + (keyboard_mouse.price if keyboard_mouse else Decimal("0"))
    )
    try:
        discount = Decimal(
            request.POST.get("discount_percent", "0").replace(",", ".").strip()
        )
    except Exception:
        discount = Decimal("0")
    if discount < 0 or discount > CalculatorSettings.MAX_DISCOUNT_PERCENT:
        discount = Decimal("0")
    markup_percent = CalculatorSettings.effective_markup_percent(discount)
    total = CalculatorSettings.apply_markup(subtotal, discount)
    markup_amount = total - subtotal

    try:
        usd_rate = Decimal(
            request.POST.get("usd_rate", "0").replace(",", ".").strip()
        )
    except Exception:
        usd_rate = Decimal("0")
    if usd_rate < 0:
        usd_rate = Decimal("0")
    total_price_uzs = (total * usd_rate).quantize(Decimal("1")) if usd_rate > 0 else Decimal("0")

    quote = BuildQuote.objects.create(
        monoblock_base=monoblock_base,
        cpu=cpu,
        ram_items=ram_items,
        storage_items=storage_items,
        keyboard_mouse=keyboard_mouse,
        subtotal_price=subtotal,
        discount_percent=discount,
        markup_percent=markup_percent,
        markup_amount=markup_amount,
        usd_rate=usd_rate,
        total_price=total,
        total_price_uzs=total_price_uzs,
    )
    quote.order_number = f"AIO#{quote.id}"
    quote.save(update_fields=["order_number"])
    return JsonResponse(
        {
            "id": quote.id,
            "order_number": quote.order_number,
            "total_price": f"{quote.total_price:.2f}",
        }
    )
