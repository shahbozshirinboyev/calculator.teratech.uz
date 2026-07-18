from datetime import timedelta
from decimal import Decimal
import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Count, Max, Q, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from orders.models import Order
from products.models import CPU, RAM, KeyboardMouse, MonoblockBase, Storage

from .models import BuildQuote, CalculatorSettings

User = get_user_model()


@login_required
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
            "markup_percent": float(settings.markup_percent),
            "max_discount_percent": settings.max_discount_percent,
            "next_order_number": f"AIO#{next_quote_id}",
            "active_nav": "aio",
        },
    )


@login_required
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


@login_required
@require_POST
def save_quote(request):
    monoblock_base = MonoblockBase.objects.get(pk=request.POST["monoblock_base"])
    cpu = CPU.objects.get(pk=request.POST["cpu"])
    keyboard_mouse_id = request.POST.get("keyboard_mouse")
    if not keyboard_mouse_id:
        return JsonResponse({"error": "Keyboard/Mouse tanlanishi kerak."}, status=400)
    keyboard_mouse = KeyboardMouse.objects.get(pk=keyboard_mouse_id)
    ram_ids = [value for value in request.POST.getlist("ram_slots") if value]
    if request.POST.get("ram"):
        ram_ids.append(request.POST["ram"])
    storage_ids = [value for value in request.POST.getlist("storage_slots") if value]
    ram_map = RAM.objects.in_bulk(ram_ids)
    storage_map = Storage.objects.in_bulk(storage_ids)
    rams = [ram_map[int(pk)] for pk in ram_ids if int(pk) in ram_map]
    storages = [storage_map[int(pk)] for pk in storage_ids if int(pk) in storage_map]

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
    settings = CalculatorSettings.get_singleton()
    if discount < 0 or discount > settings.max_discount_percent:
        discount = Decimal("0")
    markup_percent = settings.effective_markup_percent(discount)
    total = settings.apply_markup(subtotal, discount)
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


@login_required
def profile(request):
    period = request.GET.get("period", "today")
    now = timezone.localtime()

    if period == "today":
        period_filter = Q(delivered_at__date=now.date())
        period_label = "Bugungi"
    elif period == "week":
        week_start = now.date() - timedelta(days=now.weekday())
        period_filter = Q(delivered_at__date__gte=week_start)
        period_label = "Haftalik"
    elif period == "month":
        period_filter = Q(delivered_at__year=now.year, delivered_at__month=now.month)
        period_label = "Oylik"
    elif period == "year":
        period_filter = Q(delivered_at__year=now.year)
        period_label = "Yillik"
    else:
        period = "all"
        period_filter = Q()
        period_label = "Butun davr"

    completed_orders = Order.objects.filter(
        sold_by=request.user,
        production_status=Order.ProductionStatus.DELIVERED,
    ).filter(period_filter)
    stats = completed_orders.aggregate(
        total_uzs=Sum("total_price_uzs"),
        completed_orders=Count("id"),
    )
    total_uzs = stats["total_uzs"] or Decimal("0")
    completed_count = stats["completed_orders"] or 0
    users = User.objects.filter(is_active=True).order_by("first_name", "last_name", "username")

    all_time_stats = Order.objects.filter(
        sold_by=request.user,
        production_status=Order.ProductionStatus.DELIVERED,
    ).aggregate(
        total_uzs=Sum("total_price_uzs"),
        completed_orders=Count("id"),
    )
    all_time_total_uzs = all_time_stats["total_uzs"] or Decimal("0")
    all_time_completed_orders = all_time_stats["completed_orders"] or 0

    all_time_board = []
    all_time_orders = Order.objects.filter(
        production_status=Order.ProductionStatus.DELIVERED
    ).select_related("sold_by")

    for seller in users:
        seller_all_time_stats = all_time_orders.filter(sold_by=seller).aggregate(
            total_uzs=Sum("total_price_uzs"),
            completed_orders=Count("id"),
        )
        all_time_board.append(
            {
                "seller_id": seller.pk,
                "seller_name": (seller.get_full_name().strip() or seller.username),
                "total_uzs": seller_all_time_stats["total_uzs"] or Decimal("0"),
                "completed_orders": seller_all_time_stats["completed_orders"] or 0,
            }
        )

    all_time_board.sort(
        key=lambda entry: (
            -entry["total_uzs"],
            -entry["completed_orders"],
            entry["seller_name"].lower(),
        )
    )

    all_time_current_user_rank = None
    for index, entry in enumerate(all_time_board, start=1):
        if entry["seller_id"] == request.user.pk:
            all_time_current_user_rank = index
            break

    board = []
    period_orders = (
        Order.objects.filter(production_status=Order.ProductionStatus.DELIVERED)
        .filter(period_filter)
        .select_related("sold_by")
    )

    for seller in users:
        seller_stats = period_orders.filter(sold_by=seller).aggregate(
            total_uzs=Sum("total_price_uzs"),
            completed_orders=Count("id"),
        )
        seller_total_uzs = seller_stats["total_uzs"] or Decimal("0")
        seller_completed_orders = seller_stats["completed_orders"] or 0
        seller_name = seller.get_full_name().strip() or seller.username
        board.append(
            {
                "seller": seller,
                "seller_name": seller_name,
                "initial": seller_name[:1].upper(),
                "total_uzs": seller_total_uzs,
                "total_uzs_display": f"{int(seller_total_uzs):,}".replace(",", " "),
                "completed_orders": seller_completed_orders,
                "is_current_user": seller.pk == request.user.pk,
            }
        )

    board.sort(
        key=lambda entry: (
            -entry["total_uzs"],
            -entry["completed_orders"],
            entry["seller_name"].lower(),
        )
    )

    current_user_rank = None
    for index, entry in enumerate(board, start=1):
        entry["rank"] = index
        if entry["is_current_user"]:
            current_user_rank = index

    top_three = board[:3]
    top_by_rank = {entry["rank"]: entry for entry in top_three}
    podium_entries = [
        top_by_rank[rank]
        for rank in (2, 1, 3)
        if rank in top_by_rank
    ]

    return render(
        request,
        "calculator/profile.html",
        {
            "user": request.user,
            "active_nav": "profile",
            "has_admin_access": request.user.is_superuser,
            "period": period,
            "period_label": period_label,
            "stats": {
                "total_uzs": total_uzs,
                "total_uzs_display": f"{int(total_uzs):,}".replace(",", " "),
                "completed_orders": completed_count,
            },
            "all_time_stats": {
                "total_uzs": all_time_total_uzs,
                "total_uzs_display": f"{int(all_time_total_uzs):,}".replace(",", " "),
                "completed_orders": all_time_completed_orders,
            },
            "board": board,
            "top_three": top_three,
            "podium_entries": podium_entries,
            "current_user_rank": current_user_rank,
            "all_time_current_user_rank": all_time_current_user_rank,
        }
    )
