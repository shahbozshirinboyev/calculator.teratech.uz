from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Case, IntegerField, Value, When

User = get_user_model()


class Order(models.Model):
    class DeliveryType(models.TextChoices):
        DELIVERY = "DELIVERY", "Olib borish kerak"
        POST = "POST", "Pochta (BTS, UzPost, YandexGo...)"
        PICKUP = "PICKUP", "Olib ketadi"

    class PaymentType(models.TextChoices):
        CASH = "CASH", "Naqd to'lov"
        CARD = "CARD", "Kartadan to'lov"
        TRANSFER = "TRANSFER", "Bank orqali"
        CASH_CARD = "CASH_CARD", "Aralash to'lov"

    class PaymentStatus(models.TextChoices):
        UNPAID = "UNPAID", "To'lanmagan"
        ON_DELIVERY = "ON_DELIVERY", "Yetkazilganda to'lanadi"
        ON_PICKUP = "ON_PICKUP", "Olib ketishda to'lanadi"
        PARTIAL = "PARTIAL", "Qisman to'langan"
        PAID = "PAID", "To'langan"

    class ProductionStatus(models.TextChoices):
        AGREED = "AGREED", "Kelishuvda"
        QUEUED = "QUEUED", "Navbatda"
        IN_PROGRESS = "IN_PROGRESS", "Tayyorlanmoqda"
        READY = "READY", "Tayyor"
        SHIPPING = "SHIPPING", "Yo'lda"
        DELIVERED = "DELIVERED", "Yetkazildi"
        ON_HOLD = "ON_HOLD", "To'xtatildi"
        CANCELLED = "CANCELLED", "Bekor qilindi"

    DELIVERY_STATUS_FLOWS = {
        DeliveryType.DELIVERY: [
            ProductionStatus.AGREED,
            ProductionStatus.QUEUED,
            ProductionStatus.IN_PROGRESS,
            ProductionStatus.READY,
            ProductionStatus.SHIPPING,
            ProductionStatus.DELIVERED,
        ],
        DeliveryType.POST: [
            ProductionStatus.AGREED,
            ProductionStatus.QUEUED,
            ProductionStatus.IN_PROGRESS,
            ProductionStatus.READY,
            ProductionStatus.SHIPPING,
            ProductionStatus.DELIVERED,
        ],
        DeliveryType.PICKUP: [
            ProductionStatus.AGREED,
            ProductionStatus.QUEUED,
            ProductionStatus.IN_PROGRESS,
            ProductionStatus.READY,
            ProductionStatus.DELIVERED,
        ],
    }
    GLOBAL_PRODUCTION_STATUSES = [
        ProductionStatus.CANCELLED,
    ]
    DELIVERY_STATUS_LABELS = {
        DeliveryType.DELIVERY: {
            ProductionStatus.SHIPPING: "Yo'lda",
            ProductionStatus.DELIVERED: "Yetkazildi",
        },
        DeliveryType.POST: {
            ProductionStatus.SHIPPING: "Jo'natildi",
            ProductionStatus.DELIVERED: "Qabul qilib oldi",
        },
        DeliveryType.PICKUP: {
            ProductionStatus.DELIVERED: "Olib ketildi",
        },
    }

    order_number = models.CharField(
        max_length=24, unique=True, blank=True, null=True, verbose_name="Buyurtma raqami"
    )
    sold_by = models.ForeignKey(
        User, on_delete=models.PROTECT, related_name="orders", verbose_name="Sotuvchi"
    )
    customer_name = models.CharField(max_length=120, verbose_name="Mijoz ismi")
    customer_phone = models.CharField(max_length=30, verbose_name="Telefon raqami")

    # Manzil
    region = models.CharField(max_length=80, verbose_name="Viloyat")
    district = models.CharField(max_length=80, verbose_name="Tuman")
    city = models.CharField(max_length=80, verbose_name="Shahar")
    landmark = models.CharField(max_length=200, blank=True, verbose_name="Mo'ljal")

    delivery_type = models.CharField(
        max_length=20, choices=DeliveryType.choices, verbose_name="Yetkazish turi"
    )
    payment_type = models.CharField(
        max_length=20, choices=PaymentType.choices, verbose_name="To'lov turi"
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
        verbose_name="To'lov holati",
    )
    production_status = models.CharField(
        max_length=20,
        choices=ProductionStatus.choices,
        default=ProductionStatus.AGREED,
        verbose_name="Ishlab chiqarish holati",
    )

    total_price_usd = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Jami (USD)"
    )
    total_price_uzs = models.DecimalField(
        max_digits=16, decimal_places=0, default=0, verbose_name="Jami (so'm)"
    )

    delivery_date = models.DateField(null=True, blank=True, verbose_name="Yetkazib berish sanasi")
    delivery_time = models.CharField(max_length=10, null=True, blank=True, verbose_name="Yetkazib berish vaqti")
    partial_amount = models.DecimalField(
        max_digits=16, decimal_places=0, default=0, verbose_name="Qisman to'langan summa"
    )

    notes = models.TextField(blank=True, verbose_name="Izoh")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="Yetkazib berilgan vaqt")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"

    @property
    def display_order_number(self):
        raw_number = self.order_number or f"ORDER#{self.pk}"
        if raw_number.startswith("ORD#"):
            return raw_number.replace("ORD#", "ORDER#", 1)
        return raw_number

    @property
    def remaining_amount(self):
        """Qoldiq summa - jami narxdan to'langan summani ayirish"""
        if self.partial_amount:
            return self.total_price_uzs - self.partial_amount
        return self.total_price_uzs

    def __str__(self):
        return self.display_order_number

    @classmethod
    def production_status_flow(cls, delivery_type):
        return cls.DELIVERY_STATUS_FLOWS.get(
            delivery_type,
            cls.DELIVERY_STATUS_FLOWS[cls.DeliveryType.DELIVERY],
        )

    @classmethod
    def production_status_label(cls, status, delivery_type=None):
        if delivery_type:
            custom = cls.DELIVERY_STATUS_LABELS.get(delivery_type, {})
            if status in custom:
                return custom[status]
        return dict(cls.ProductionStatus.choices).get(status, status)

    @classmethod
    def production_status_choices_for_delivery(cls, delivery_type):
        statuses = list(cls.production_status_flow(delivery_type))
        for status in cls.GLOBAL_PRODUCTION_STATUSES:
            if status not in statuses:
                statuses.append(status)
        return [(status, cls.production_status_label(status, delivery_type)) for status in statuses]

    @classmethod
    def queue_queryset(cls):
        """Navbat: DELIVERED va CANCELLED dan tashqari, ustuvorlik + created_at tartibida."""
        priority = Case(
            When(payment_status=cls.PaymentStatus.PAID, then=Value(0)),
            When(payment_status=cls.PaymentStatus.PARTIAL, then=Value(1)),
            When(
                payment_status__in=[cls.PaymentStatus.ON_DELIVERY, cls.PaymentStatus.ON_PICKUP],
                then=Value(2),
            ),
            When(payment_status=cls.PaymentStatus.UNPAID, then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        )
        return (
            cls.objects.exclude(
                production_status__in=[cls.ProductionStatus.DELIVERED, cls.ProductionStatus.CANCELLED]
            )
            .annotate(priority=priority)
            .order_by("priority", "created_at")
        )


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    build_quote = models.ForeignKey(
        "calculator.BuildQuote",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="order_items",
        verbose_name="Kalkulyator konfiguratsiyasi",
    )
    config_label = models.CharField(max_length=255, verbose_name="Konfiguratsiya")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Soni")
    unit_price_usd = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Dona narxi (USD)"
    )
    unit_price_uzs = models.DecimalField(
        max_digits=16, decimal_places=2, default=0, verbose_name="Dona narxi (so'm)"
    )

    class Meta:
        verbose_name = "Buyurtma elementi"
        verbose_name_plural = "Buyurtma elementlari"

    def __str__(self):
        return f"{self.config_label} x{self.quantity}"

    @property
    def line_total_usd(self):
        return self.unit_price_usd * self.quantity
