from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Case, IntegerField, Value, When

User = get_user_model()


class Order(models.Model):
    class DeliveryType(models.TextChoices):
        BTS = "BTS", "BTS"
        UZPOST = "UZPOST", "UZPOST"
        PICKUP = "PICKUP", "Olib ketadi"
        DELIVERY = "DELIVERY", "Olib borish kerak"

    class PaymentType(models.TextChoices):
        CARD = "CARD", "Karta"
        CASH = "CASH", "Naqt"
        TRANSFER = "TRANSFER", "Pul ko'chirish"
        CASH_CARD = "CASH_CARD", "Naqt + Karta"

    class PaymentStatus(models.TextChoices):
        PAID = "PAID", "To'langan"
        ON_DELIVERY = "ON_DELIVERY", "Yetkazilganda"
        PARTIAL = "PARTIAL", "Qisman"

    class ProductionStatus(models.TextChoices):
        QUEUED = "QUEUED", "Navbatda"
        IN_PROGRESS = "IN_PROGRESS", "Yig'ilmoqda"
        READY = "READY", "Tayyor"
        SHIPPING = "SHIPPING", "Yetkazilmoqda"
        DELIVERED = "DELIVERED", "Yetkazib berildi"
        CANCELLED = "CANCELLED", "Bekor qilindi"

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
        default=PaymentStatus.ON_DELIVERY,
        verbose_name="To'lov holati",
    )
    production_status = models.CharField(
        max_length=20,
        choices=ProductionStatus.choices,
        default=ProductionStatus.QUEUED,
        verbose_name="Ishlab chiqarish holati",
    )

    total_price_usd = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, verbose_name="Jami (USD)"
    )
    total_price_uzs = models.DecimalField(
        max_digits=16, decimal_places=0, default=0, verbose_name="Jami (so'm)"
    )

    notes = models.TextField(blank=True, verbose_name="Izoh")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="Yetkazib berilgan vaqt")

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"

    def __str__(self):
        return self.order_number or f"ORD#{self.pk}"

    @classmethod
    def queue_queryset(cls):
        """Navbat: DELIVERED va CANCELLED dan tashqari, ustuvorlik + created_at tartibida."""
        priority = Case(
            When(payment_status=cls.PaymentStatus.PAID, then=Value(0)),
            When(payment_status=cls.PaymentStatus.PARTIAL, then=Value(1)),
            When(payment_status=cls.PaymentStatus.ON_DELIVERY, then=Value(2)),
            default=Value(3),
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

    class Meta:
        verbose_name = "Buyurtma elementi"
        verbose_name_plural = "Buyurtma elementlari"

    def __str__(self):
        return f"{self.config_label} x{self.quantity}"

    @property
    def line_total_usd(self):
        return self.unit_price_usd * self.quantity
