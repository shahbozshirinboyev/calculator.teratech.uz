from django import template
from orders.models import Order

register = template.Library()

STATUS_BADGE = {
    "AGREED": "badge-on-del",
    "QUEUED": "badge-queued",
    "IN_PROGRESS": "badge-in-progress",
    "READY": "badge-ready",
    "SHIPPING": "badge-shipping",
    "DELIVERED": "badge-delivered",
    "ON_HOLD": "badge-on-del",
    "CANCELLED": "badge-cancelled",
}

STATUS_ICONS = {
    "AGREED": "🤝",
    "QUEUED": "📋",
    "IN_PROGRESS": "🛠️",
    "READY": "✅",
    "SHIPPING": "🚚",
    "DELIVERED": "✔️",
    "ON_HOLD": "⏸️",
    "CANCELLED": "❌",
}

PAYMENT_BADGE = {
    "PAID": "badge-paid",
    "PARTIAL": "badge-partial",
    "ON_DELIVERY": "badge-on-del",
    "ON_PICKUP": "badge-on-del",
    "UNPAID": "badge-on-del",
}


@register.filter
def status_badge(value):
    return STATUS_BADGE.get(value, "")


@register.filter
def status_icon(value):
    return STATUS_ICONS.get(value, "📦")


@register.filter
def payment_badge(value):
    return PAYMENT_BADGE.get(value, "")


@register.filter
def next_status_for(value, delivery_type):
    try:
        status_flow = Order.production_status_flow(delivery_type)
        idx = status_flow.index(value)
        return status_flow[idx + 1] if idx + 1 < len(status_flow) else None
    except (ValueError, IndexError):
        return None


@register.filter
def status_label(value, delivery_type=None):
    return Order.production_status_label(value, delivery_type)


@register.simple_tag
def order_status_flow(order):
    return Order.production_status_flow(order.delivery_type)


@register.simple_tag
def order_status_index(order):
    flow = Order.production_status_flow(order.delivery_type)
    try:
        return flow.index(order.production_status)
    except ValueError:
        return -1


@register.filter
def format_phone(value):
    if not value:
        return ''
    # Keep only digits
    digits = ''.join(c for c in str(value) if c.isdigit())

    # If it's a 9-digit number, e.g. 901234567
    if len(digits) == 9:
        return f'+998 ({digits[0:2]}) {digits[2:5]}-{digits[5:7]}-{digits[7:9]}'
    # If it already includes 998 and is 12 digits, e.g. 998901234567
    elif len(digits) == 12 and digits.startswith('998'):
        return f'+998 ({digits[3:5]}) {digits[5:8]}-{digits[8:10]}-{digits[10:12]}'
    # Otherwise return original formatted nicely or clean digits
    return value


@register.filter
def format_uzs(value):
    if not value:
        return '0'
    try:
        num = int(float(value))
        # Format with thousands separators using spaces
        s = str(num)
        result = []
        for i, c in enumerate(reversed(s)):
            if i and i % 3 == 0:
                result.append(' ')
            result.append(c)
        return ''.join(reversed(result))
    except (ValueError, TypeError):
        return value


@register.filter
def remaining(total, paid):
    if not total:
        total = 0
    if not paid:
        paid = 0
    try:
        total = float(total)
        paid = float(paid)
        return total - paid
    except (ValueError, TypeError):
        return 0
