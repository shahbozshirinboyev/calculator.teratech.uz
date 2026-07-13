from django import template

register = template.Library()

STATUS_FLOW = ["QUEUED", "IN_PROGRESS", "READY", "SHIPPING", "DELIVERED"]

STATUS_LABELS = {
    "QUEUED": "Navbatda",
    "IN_PROGRESS": "Yig'ilmoqda",
    "READY": "Tayyor",
    "SHIPPING": "Yetkazilmoqda",
    "DELIVERED": "Yetkazib berildi",
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
