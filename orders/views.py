import json
from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Order, OrderItem

User = get_user_model()

def _can_user_view_all_orders(user):
    return user.is_superuser or user.has_perm("orders.view_order") or user.has_perm("orders.change_order") or user.has_perm("orders.delete_order")


def _can_user_edit_order(user, order):
    return user.is_superuser or user.has_perm("orders.change_order") or order.sold_by_id == user.id


def _can_user_delete_order(user):
    return user.is_superuser or user.has_perm("orders.delete_order")


def _can_user_cancel_order(user, order):
    return _can_user_set_production_status(
        user,
        Order.ProductionStatus.CANCELLED,
        order.production_status,
        order,
    )


def _parse_decimal(value, default=Decimal("0")):
    try:
        return Decimal(str(value).replace(",", ".").strip())
    except (InvalidOperation, TypeError):
        return default


def _orders_for_user(user):
    qs = Order.objects.all()
    if _can_user_view_all_orders(user):
        return qs
    return qs.filter(sold_by=user)


def _serialize_choices(choices):
    return [{"value": value, "label": label} for value, label in choices]


def _can_user_change_production_status(user, current_status=None, order=None):
    if user.is_superuser or user.has_perm("orders.change_order"):
        return True
    if order is not None and order.sold_by_id != user.id:
        return False
    if not current_status:
        return True
    return current_status in {
        Order.ProductionStatus.AGREED,
        Order.ProductionStatus.QUEUED,
    }


def _allowed_production_status_choices_for_user(user, delivery_type, current_status=None, order=None):
    choices = Order.production_status_choices_for_delivery(delivery_type)
    if user.is_superuser or user.has_perm("orders.change_order"):
        return choices
    if not _can_user_change_production_status(user, current_status, order):
        return []
    allowed_statuses = {
        Order.ProductionStatus.AGREED,
        Order.ProductionStatus.QUEUED,
    }
    return [(value, label) for value, label in choices if value in allowed_statuses]


def _all_production_status_choices_map(delivery_type):
    return dict(Order.production_status_choices_for_delivery(delivery_type))


def _can_user_set_production_status(user, target_status, current_status=None, order=None):
    if user.is_superuser or user.has_perm("orders.change_order"):
        return True
    if order is not None and order.sold_by_id != user.id:
        return False
    allowed_statuses = {
        Order.ProductionStatus.AGREED,
        Order.ProductionStatus.QUEUED,
    }
    if not current_status:
        return target_status in allowed_statuses
    if current_status in allowed_statuses:
        return target_status in allowed_statuses
    return bool(current_status) and target_status == current_status


def _production_status_groups_json_for_user(user):
    groups = {}
    for delivery_type, _ in Order.DeliveryType.choices:
        groups[delivery_type] = _serialize_choices(
            _allowed_production_status_choices_for_user(user, delivery_type)
        )
    return json.dumps(groups, ensure_ascii=False)


def _all_production_status_groups_json():
    groups = {}
    for delivery_type, _ in Order.DeliveryType.choices:
        groups[delivery_type] = _serialize_choices(
            Order.production_status_choices_for_delivery(delivery_type)
        )
    return json.dumps(groups, ensure_ascii=False)


def _attach_order_permissions(user, orders):
    for order in orders:
        order.card_can_edit = _can_user_edit_order(user, order)
        order.card_can_delete = _can_user_delete_order(user)
        order.card_can_change_status = _can_user_change_production_status(
            user,
            order.production_status,
            order,
        )
        order.card_status_choices = _allowed_production_status_choices_for_user(
            user,
            order.delivery_type,
            order.production_status,
            order,
        )
    return orders


def _format_filter_date(value):
    if not value:
        return ""
    try:
        from datetime import datetime
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return value


def _order_status_tabs():
    return [
        {"value": "ALL", "icon": "📦", "label": "Barchasi"},
        {"value": Order.ProductionStatus.AGREED, "icon": "🤝", "label": "Kelishuvda"},
        {"value": Order.ProductionStatus.QUEUED, "icon": "📋", "label": "Navbatda"},
        {"value": Order.ProductionStatus.IN_PROGRESS, "icon": "🛠️", "label": "Tayyorlanmoqda"},
        {"value": Order.ProductionStatus.READY, "icon": "✅", "label": "Tayyor"},
        {"value": Order.ProductionStatus.SHIPPING, "icon": "🚚", "label": "Yetkazilmoqda"},
        {"value": Order.ProductionStatus.DELIVERED, "icon": "✔️", "label": "Yakunlandi"},
        {"value": Order.ProductionStatus.ON_HOLD, "icon": "⏸️", "label": "To'xtatildi"},
        {"value": Order.ProductionStatus.CANCELLED, "icon": "❌", "label": "Bekor qilindi"},
    ]


@login_required
def order_list(request):
    from calculator.models import CalculatorSettings
    from django.utils import timezone
    from collections import defaultdict

    # USD kursini olish
    try:
        settings = CalculatorSettings.objects.first()
        usd_rate = int(settings.usd_rate) if settings and settings.usd_rate else 12850
    except:
        usd_rate = 12850

    status_tabs = _order_status_tabs()
    valid_status_values = {item["value"] for item in status_tabs}
    selected_status = request.GET.get("status_tab", "ALL")
    if selected_status not in valid_status_values:
        selected_status = "ALL"

    # Base querysets: if superuser, show all; else only own orders
    can_view_all_orders = _can_user_view_all_orders(request.user)

    if can_view_all_orders:
        orders_qs = Order.objects.all().prefetch_related("items").select_related("sold_by").order_by("-updated_at")
    else:
        orders_qs = Order.objects.filter(sold_by=request.user).prefetch_related("items").select_related("sold_by").order_by("-updated_at")

    # Common filters
    sold_by = request.GET.get("sold_by")
    delivery_type = request.GET.get("delivery_type")
    payment_status = request.GET.get("payment_status")
    date_from = request.GET.get("date_from")
    date_to = request.GET.get("date_to")

    def apply_filters(qs):
        if sold_by and can_view_all_orders:
            qs = qs.filter(sold_by_id=sold_by)
        if delivery_type:
            qs = qs.filter(delivery_type=delivery_type)
        if payment_status:
            qs = qs.filter(payment_status=payment_status)
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        return qs

    filtered_qs = apply_filters(orders_qs)

    status_counts_map = {}
    for item in status_tabs:
        if item["value"] == "ALL":
            status_counts_map[item["value"]] = filtered_qs.count()
        else:
            status_counts_map[item["value"]] = filtered_qs.filter(production_status=item["value"]).count()

    if selected_status == "ALL":
        selected_qs = filtered_qs
    else:
        selected_qs = filtered_qs.filter(production_status=selected_status)

    # Group orders by date
    def group_by_date(orders):
        groups = defaultdict(list)
        today = timezone.now().date()
        for order in orders:
            order_date = order.created_at.date()
            groups[order_date].append(order)
        # Sort each group by created_at time (newest first within the day)
        for date in groups:
            groups[date].sort(key=lambda x: x.created_at, reverse=True)
        # Sort groups by date descending
        sorted_groups = sorted(groups.items(), key=lambda x: x[0], reverse=True)
        # Add "is_today" flag
        return [(date, _attach_order_permissions(request.user, orders), date == today) for date, orders in sorted_groups]

    status_groups = group_by_date(selected_qs)

    # For superusers, show all regular sellers in filter; for others, no seller filter
    if can_view_all_orders:
        sellers = User.objects.filter(is_superuser=False).order_by("first_name", "username")
    else:
        sellers = []

    return render(request, "orders/order_list.html", {
        "active_nav": "orders",
        "status_tab": selected_status,
        "selected_status_label": next((item["label"] for item in status_tabs if item["value"] == selected_status), ""),
        "status_groups": status_groups,
        "status_tabs": [
            {
                **item,
                "count": status_counts_map.get(item["value"], 0),
            }
            for item in status_tabs
        ],
        "sellers": sellers,
        "can_view_all_orders": can_view_all_orders,
        "usd_rate": usd_rate,
        "filters": {
            "status_tab": selected_status,
            "sold_by": sold_by,
            "delivery_type": delivery_type,
            "payment_status": payment_status,
            "date_from": date_from,
            "date_to": date_to,
            "date_from_display": _format_filter_date(date_from),
            "date_to_display": _format_filter_date(date_to),
        },
        "delivery_choices": Order.DeliveryType.choices,
        "payment_status_choices": Order.PaymentStatus.choices,
        "production_status_choices": Order.production_status_choices_for_delivery(Order.DeliveryType.DELIVERY),
    })


def _form_context(user, order, initial, extra=None):
    """order_form.html uchun umumiy context yasaydi."""
    from calculator.models import CalculatorSettings

    # USD kursini olish
    try:
        settings = CalculatorSettings.objects.first()
        usd_rate = int(settings.usd_rate) if settings and settings.usd_rate else 12850
    except:
        usd_rate = 12850

    src = initial or {}
    o = order  # None yoki Order instance

    # Get values
    v_delivery_type = src.get("delivery_type", getattr(o, "delivery_type", ""))
    v_payment_type = src.get("payment_type", getattr(o, "payment_type", ""))
    v_payment_status = src.get("payment_status", getattr(o, "payment_status", ""))
    v_production_status = src.get("production_status", getattr(o, "production_status", ""))

    # Create choice label maps
    delivery_label_map = dict(Order.DeliveryType.choices)
    payment_type_label_map = dict(Order.PaymentType.choices)
    payment_status_label_map = dict(Order.PaymentStatus.choices)
    all_production_status_label_map = dict(
        Order.production_status_choices_for_delivery(v_delivery_type or Order.DeliveryType.DELIVERY)
    )
    production_status_choices = _allowed_production_status_choices_for_user(
        user,
        v_delivery_type or Order.DeliveryType.DELIVERY,
        getattr(o, "production_status", None),
        o,
    )

    raw_delivery_time = src.get("delivery_time", getattr(o, "delivery_time", ""))
    if hasattr(raw_delivery_time, "strftime"):
        formatted_delivery_time = raw_delivery_time.strftime("%H:%M")
    elif isinstance(raw_delivery_time, str):
        formatted_delivery_time = raw_delivery_time[:5] if raw_delivery_time else ""
    else:
        formatted_delivery_time = str(raw_delivery_time)[:5] if raw_delivery_time else ""

    ctx = {
        "v_customer_name":  src.get("customer_name",  getattr(o, "customer_name",  "")),
        "v_customer_phone": src.get("customer_phone", getattr(o, "customer_phone", "")),
        "v_region":         src.get("region",         getattr(o, "region",         "")),
        "v_district":       src.get("district",       getattr(o, "district",       "")),
        "v_city":           src.get("city",            getattr(o, "city",           "")),
        "v_landmark":       src.get("landmark",       getattr(o, "landmark",       "")),
        "v_delivery_type":  v_delivery_type,
        "v_delivery_type_label": delivery_label_map.get(v_delivery_type, ""),
        "v_payment_type":   v_payment_type,
        "v_payment_type_label": payment_type_label_map.get(v_payment_type, ""),
        "v_payment_status": v_payment_status,
        "v_payment_status_label": payment_status_label_map.get(v_payment_status, ""),
        "v_production_status": v_production_status,
        "v_production_status_label": all_production_status_label_map.get(v_production_status, ""),
        "v_delivery_date":  src.get("delivery_date", str(getattr(o, "delivery_date", "")) if getattr(o, "delivery_date", None) else ""),
        "v_delivery_time":  formatted_delivery_time,
        "v_partial_amount": src.get("partial_amount", str(getattr(o, "partial_amount", "0"))),
        "v_total_usd":      src.get("total_price_usd",str(getattr(o, "total_price_usd", "0"))),
        "v_total_uzs":      src.get("total_price_uzs",str(getattr(o, "total_price_uzs", "0"))),
        "v_notes":          src.get("notes",          getattr(o, "notes",          "")),
        "order": o,
        "usd_rate": usd_rate,  # USD kursini qo'shamiz
        "active_nav": "orders",
        "delivery_choices": Order.DeliveryType.choices,
        "payment_type_choices": Order.PaymentType.choices,
        "payment_status_choices": Order.PaymentStatus.choices,
        "production_status_choices": production_status_choices,
        "production_status_groups_json": _production_status_groups_json_for_user(user),
        "all_production_status_groups_json": _all_production_status_groups_json(),
        "can_edit_production_status": _can_user_change_production_status(
            user,
            getattr(o, "production_status", None),
            o,
        ),
    }

    # URL parametrlaridan kelgan items ma'lumotlarini qo'shish
    if "items" in src:
        ctx["initial_items"] = src["items"]

    if extra:
        ctx.update(extra)
    return ctx


@login_required
def order_create(request):
    if request.method == "POST":
        try:
            order = _save_order(request, instance=None)
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({
                    "ok": True,
                    "order_id": order.pk,
                    "order_number": order.display_order_number,
                    "redirect": f"/orders/{order.pk}/",
                })
            return redirect("orders:detail", pk=order.pk)
        except ValueError as e:
            error = str(e)
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"ok": False, "error": error}, status=400)
            return render(request, "orders/order_form.html",
                          _form_context(request.user, None, request.POST, {"error": error}))

    # GET request - URL parametrlaridan ma'lumotlarni olish
    initial = {}
    if request.GET:
        config_labels = request.GET.getlist("config_label")
        quantities = request.GET.getlist("quantity")
        unit_prices_uzs = request.GET.getlist("unit_price_uzs")

        if config_labels:
            items_data = []
            for i, label in enumerate(config_labels):
                qty = int(quantities[i]) if i < len(quantities) and quantities[i].isdigit() else 1
                price_uzs = _parse_decimal(unit_prices_uzs[i] if i < len(unit_prices_uzs) else "0")

                # So'mdan USD ga konvertatsiya qilish
                try:
                    from calculator.models import CalculatorSettings
                    settings = CalculatorSettings.objects.first()
                    usd_rate = settings.usd_rate if settings and settings.usd_rate else Decimal("12850")
                    price_usd = price_uzs / usd_rate if usd_rate > 0 else Decimal("0")
                except:
                    price_usd = Decimal("0")

                items_data.append({
                    "config_label": label,
                    "quantity": qty,
                    "unit_price_usd": price_usd,
                    "unit_price_uzs": price_uzs
                })
            initial["items"] = items_data

        total_uzs = request.GET.get("total_price_uzs", "")
        initial["total_price_uzs"] = total_uzs

        # USD ga konvertatsiya
        if total_uzs:
            try:
                from calculator.models import CalculatorSettings
                settings = CalculatorSettings.objects.first()
                usd_rate = settings.usd_rate if settings and settings.usd_rate else Decimal("12850")
                total_usd = _parse_decimal(total_uzs) / usd_rate if usd_rate > 0 else Decimal("0")
                initial["total_price_usd"] = str(total_usd)
            except:
                pass

    return render(request, "orders/order_form.html", _form_context(request.user, None, initial))


@login_required
def order_detail(request, pk):
    from calculator.models import CalculatorSettings

    # USD kursini olish
    try:
        settings = CalculatorSettings.objects.first()
        usd_rate = int(settings.usd_rate) if settings and settings.usd_rate else 12850
    except:
        usd_rate = 12850

    order = get_object_or_404(
        _orders_for_user(request.user).prefetch_related("items").select_related("sold_by"),
        pk=pk,
    )
    if request.method == "GET" and request.GET.get("edit") == "1":
        if not _can_user_edit_order(request.user, order):
            raise PermissionDenied("Sizda buyurtmani tahrirlash huquqi yo'q.")
        return render(request, "orders/order_form.html", _form_context(request.user, order, {}))

    if request.method == "POST":
        if not _can_user_edit_order(request.user, order):
            raise PermissionDenied("Sizda buyurtmani tahrirlash huquqi yo'q.")
        try:
            _save_order(request, instance=order)
            return redirect("orders:list")
        except ValueError as e:
            error = str(e)
            return render(request, "orders/order_form.html",
                          _form_context(request.user, order, request.POST, {"error": error}))

    allowed_production_status_choices = _allowed_production_status_choices_for_user(
        request.user,
        order.delivery_type,
        order.production_status,
        order,
    )
    allowed_production_status_values = {value for value, _ in allowed_production_status_choices}

    return render(request, "orders/order_detail.html", {
        "active_nav": "orders",
        "order": order,
        "usd_rate": usd_rate,
        "status_flow": Order.production_status_flow(order.delivery_type),
        "current_status_index": (
            Order.production_status_flow(order.delivery_type).index(order.production_status)
            if order.production_status in Order.production_status_flow(order.delivery_type)
            else -1
        ),
        "delivery_choices": Order.DeliveryType.choices,
        "payment_type_choices": Order.PaymentType.choices,
        "payment_status_choices": Order.PaymentStatus.choices,
        "production_status_choices": allowed_production_status_choices,
        "can_edit_order": _can_user_edit_order(request.user, order),
        "can_delete_order": _can_user_delete_order(request.user),
        "can_cancel_order": _can_user_cancel_order(request.user, order),
        "can_change_production_status": _can_user_change_production_status(
            request.user,
            order.production_status,
            order,
        ),
        "show_current_status_option": order.production_status not in allowed_production_status_values,
        "current_status_label": _all_production_status_choices_map(order.delivery_type).get(
            order.production_status,
            order.production_status,
        ),
    })


@login_required
@require_POST
def order_update_status(request, pk):
    order = get_object_or_404(_orders_for_user(request.user), pk=pk)
    new_status = request.POST.get("status")
    valid = [s for s, _ in Order.production_status_choices_for_delivery(order.delivery_type)]
    if new_status not in valid:
        return JsonResponse({"error": "Noto'g'ri status."}, status=400)
    if not _can_user_set_production_status(request.user, new_status, order.production_status, order):
        return JsonResponse(
            {"error": "Siz bu buyurtma uchun ushbu statusni o'zgartira olmaysiz."},
            status=403,
        )
    order.production_status = new_status
    if new_status == Order.ProductionStatus.DELIVERED:
        order.delivered_at = timezone.now()
    order.save(update_fields=["production_status", "delivered_at", "updated_at"])
    response_data = {
        "status": order.production_status,
        "status_label": Order.production_status_label(order.production_status, order.delivery_type),
    }
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(response_data)
    return redirect("orders:detail", pk=order.pk)


@login_required
def order_delete(request, pk):
    if not _can_user_delete_order(request.user):
        raise PermissionDenied("Sizda buyurtmani o'chirish huquqi yo'q.")

    order = get_object_or_404(_orders_for_user(request.user), pk=pk)
    if request.method == "POST":
        order.delete()
        return redirect("orders:list")
    return redirect("orders:detail", pk=pk)


@login_required
def leaderboard(request):
    period = request.GET.get("period", "today")
    now = timezone.now()

    if period == "today":
        date_filter = Q(created_at__date=now.date())
    elif period == "week":
        week_start = now.date() - timezone.timedelta(days=now.weekday())
        date_filter = Q(created_at__date__gte=week_start)
    elif period == "month":
        date_filter = Q(created_at__year=now.year, created_at__month=now.month)
    else:
        date_filter = Q()

    active_filter = date_filter & ~Q(production_status=Order.ProductionStatus.CANCELLED)
    cancelled_filter = date_filter & Q(production_status=Order.ProductionStatus.CANCELLED)

    sellers = User.objects.filter(
        is_superuser=False,
        orders__isnull=False
    ).distinct()

    board = []
    for seller in sellers:
        agg = Order.objects.filter(active_filter, sold_by=seller).aggregate(
            total_usd=Sum("total_price_usd"),
            total_uzs=Sum("total_price_uzs"),
            order_count=Count("id"),
        )
        units = OrderItem.objects.filter(
            order__sold_by=seller,
            order__in=Order.objects.filter(active_filter, sold_by=seller),
        ).aggregate(total_units=Sum("quantity"))["total_units"] or 0

        cancelled = Order.objects.filter(cancelled_filter, sold_by=seller).count()

        board.append({
            "seller": seller,
            "total_usd": agg["total_usd"] or Decimal("0"),
            "total_uzs": agg["total_uzs"] or Decimal("0"),
            "order_count": agg["order_count"] or 0,
            "units_sold": units,
            "cancelled": cancelled,
        })

    board.sort(key=lambda x: (x["units_sold"], x["total_usd"]), reverse=True)

    return render(request, "orders/leaderboard.html", {
        "active_nav": "orders",
        "board": board,
        "period": period,
    })


@login_required
def seller_profile(request):
    profile_url = redirect("calculator:profile")
    query_string = request.GET.urlencode()
    if query_string:
        profile_url["Location"] = f"{profile_url['Location']}?{query_string}"
    return profile_url


def _save_order(request, instance=None):
    """Create or update an Order + its OrderItems from POST data."""
    post = request.POST

    customer_name = post.get("customer_name", "").strip()
    customer_phone = post.get("customer_phone", "").strip()
    region = post.get("region", "").strip()
    district = post.get("district", "").strip()
    city = post.get("city", "").strip()
    landmark = post.get("landmark", "").strip()
    delivery_type = post.get("delivery_type", "").strip()
    payment_type = post.get("payment_type", "").strip()
    payment_status = post.get("payment_status", "").strip()
    production_status = post.get("production_status", "").strip()
    if not production_status:
        production_status = getattr(instance, "production_status", "") or Order.ProductionStatus.AGREED

    delivery_date_str = post.get("delivery_date", "").strip()
    delivery_time = post.get("delivery_time", "").strip()
    partial_amount_str = post.get("partial_amount", "0").strip()

    notes = post.get("notes", "").strip()

    errors = []

    delivery_date = None
    if delivery_date_str:
        from datetime import datetime
        try:
            delivery_date = datetime.strptime(delivery_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    clean_partial = "".join(c for c in partial_amount_str if c.isdigit() or c in ".,")
    partial_amount = _parse_decimal(clean_partial, Decimal("0"))

    if not customer_name:
        errors.append("Mijoz ismi kiritilmadi.")
    if not customer_phone:
        errors.append("Telefon raqami kiritilmadi.")
    if not region:
        errors.append("Viloyat kiritilmadi.")
    if not district:
        errors.append("Tuman kiritilmadi.")
    if delivery_type not in [d for d, _ in Order.DeliveryType.choices]:
        errors.append("Yetkazish turi tanlanmadi.")
    if payment_type not in [p for p, _ in Order.PaymentType.choices]:
        errors.append("To'lov turi tanlanmadi.")
    if payment_status not in [p for p, _ in Order.PaymentStatus.choices]:
        errors.append("To'lov statusi tanlanmadi.")
    valid_production_statuses = [s for s, _ in Order.production_status_choices_for_delivery(delivery_type)]
    if production_status not in valid_production_statuses:
        errors.append("Status tanlovi yetkazish turiga mos emas.")
    if not _can_user_set_production_status(
        request.user,
        production_status,
        getattr(instance, "production_status", None),
        instance,
    ):
        errors.append("Siz bu buyurtma uchun ushbu statusni o'zgartira olmaysiz.")
    if delivery_type and (not delivery_date or not delivery_time):
        errors.append("Yetkazib berish sanasi va vaqti kiritilmadi.")

    config_labels = post.getlist("config_label")
    quantities = post.getlist("quantity")
    unit_prices_uzs = post.getlist("unit_price_uzs")

    items_data = []
    total_price_uzs = Decimal("0")
    # Get USD rate once for all calculations
    try:
        from calculator.models import CalculatorSettings
        settings = CalculatorSettings.objects.first()
        usd_rate = settings.usd_rate if settings and settings.usd_rate else Decimal("12850")
    except:
        usd_rate = Decimal("12850")

    for i, label in enumerate(config_labels):
        label = label.strip()
        if not label:
            continue
        qty = int(quantities[i]) if i < len(quantities) and quantities[i].isdigit() else 1
        price_uzs = _parse_decimal(unit_prices_uzs[i] if i < len(unit_prices_uzs) else "0")

        # So'mdan USD ga konvertatsiya qilish (database uchun)
        price_usd = price_uzs / usd_rate if usd_rate > 0 else Decimal("0")

        items_data.append({"config_label": label, "quantity": qty, "unit_price_usd": price_usd, "unit_price_uzs": price_uzs})
        total_price_uzs += price_uzs * qty

    total_price_usd = total_price_uzs / usd_rate if usd_rate > 0 else Decimal("0")

    if not items_data:
        errors.append("Kamida bitta mahsulot qo'shing.")

    if errors:
        raise ValueError(" | ".join(errors))

    if instance is None:
        order = Order(sold_by=request.user)
    else:
        order = instance

    order.customer_name = customer_name
    order.customer_phone = customer_phone
    order.region = region
    order.district = district
    order.city = city
    order.landmark = landmark
    order.delivery_type = delivery_type
    order.payment_type = payment_type
    order.payment_status = payment_status
    order.production_status = production_status
    order.total_price_usd = total_price_usd
    order.total_price_uzs = total_price_uzs
    order.delivery_date = delivery_date
    order.delivery_time = delivery_time
    order.partial_amount = partial_amount if payment_status == Order.PaymentStatus.PARTIAL else Decimal("0")
    order.notes = notes

    if order.production_status == Order.ProductionStatus.DELIVERED and not order.delivered_at:
        order.delivered_at = timezone.now()

    order.save()

    if not order.order_number:
        order.order_number = f"ORDER#{order.pk}"
        order.save(update_fields=["order_number"])

    # Replace items
    order.items.all().delete()
    for item in items_data:
        OrderItem.objects.create(order=order, **item)

    return order
