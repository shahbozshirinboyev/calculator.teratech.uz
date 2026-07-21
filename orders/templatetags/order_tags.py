from django import template

register = template.Library()

STATUS_FLOW = ["QUEUED", "IN_PROGRESS", "READY", "DELIVERED"]

STATUS_LABELS = {
    "QUEUED": "Navbatda",
    "IN_PROGRESS": "Tayyorlanmoqda",
    "READY": "Tayyor",
    "DELIVERED": "Yetkazildi",
    "CANCELLED": "Bekor qilindi",
}

STATUS_BADGE = {
    "QUEUED": "badge-queued",
    "IN_PROGRESS": "badge-in-progress",
    "READY": "badge-ready",
    "SHIPPING": "badge-shipping",
    "DELIVERED": "badge-delivered",
    "CANCELLED": "badge-cancelled",
}

PAYMENT_BADGE = {
    "PAID": "badge-paid",
    "PARTIAL": "badge-partial",
    "ON_DELIVERY": "badge-on-del",
}


@register.filter
def status_badge(value):
    return STATUS_BADGE.get(value, "")


@register.filter
def payment_badge(value):
    return PAYMENT_BADGE.get(value, "")


@register.filter
def next_status(value):
    try:
        idx = STATUS_FLOW.index(value)
        return STATUS_FLOW[idx + 1] if idx + 1 < len(STATUS_FLOW) else None
    except (ValueError, IndexError):
        return None


@register.filter
def status_label(value):
    return STATUS_LABELS.get(value, value)


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
