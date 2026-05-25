from django.db import models

from products.models import CPU, KeyboardMouse, MonoblockBase


class CalculatorSettings(models.Model):
    MARKUP_PERCENT = 10
    MAX_DISCOUNT_PERCENT = 7
    MIN_MARKUP_PERCENT = 3

    usd_rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Dollar kursi (so'm)",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Kalkulyator sozlamalari"
        verbose_name_plural = "Kalkulyator sozlamalari"

    def __str__(self):
        return f"Dollar kursi: {self.usd_rate}"

    @classmethod
    def get_singleton(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"usd_rate": 0})
        return obj

    @classmethod
    def effective_markup_percent(cls, discount_percent=0):
        from decimal import Decimal

        discount = min(
            max(Decimal("0"), Decimal(str(discount_percent))),
            Decimal(str(cls.MAX_DISCOUNT_PERCENT)),
        )
        return max(
            Decimal(str(cls.MIN_MARKUP_PERCENT)),
            Decimal(str(cls.MARKUP_PERCENT)) - discount,
        )

    @classmethod
    def apply_markup(cls, subtotal, discount_percent=0):
        from decimal import Decimal

        markup = cls.effective_markup_percent(discount_percent)
        return subtotal * (Decimal("1") + markup / Decimal("100"))


class BuildQuote(models.Model):
    monoblock_base = models.ForeignKey(MonoblockBase, on_delete=models.PROTECT, related_name="quotes")
    cpu = models.ForeignKey(CPU, on_delete=models.PROTECT, related_name="quotes")
    ram_items = models.JSONField(default=list, blank=True)
    storage_items = models.JSONField(default=list, blank=True)
    keyboard_mouse = models.ForeignKey(
        KeyboardMouse,
        on_delete=models.PROTECT,
        related_name="quotes",
        blank=True,
        null=True,
    )
    subtotal_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Sof narx (USD)",
    )
    discount_percent = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0,
        verbose_name="Chegirma (%)",
    )
    markup_percent = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=10,
        verbose_name="Ustama (%)",
    )
    markup_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Ustama summasi (USD)",
    )
    usd_rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Dollar kursi (so'm)",
    )
    total_price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Jami (USD)")
    total_price_uzs = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name="Jami (so'm)",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Saved Calculation"
        verbose_name_plural = "Saved Calculations"

    def __str__(self):
        return f"{self.monoblock_base} - {self.total_price}"
