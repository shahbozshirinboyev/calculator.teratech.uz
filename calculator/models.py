from django.db import models

from products.models import CPU, KeyboardMouse, MonoblockBase


class CalculatorSettings(models.Model):
    usd_rate = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="Dollar kursi (so'm)",
    )
    markup_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10,
        verbose_name="AIO ustama (%)",
    )
    branded_aio_markup_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10,
        verbose_name="Branded AIO ustama (%)",
    )
    branded_pc_markup_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10,
        verbose_name="Branded PC ustama (%)",
    )
    monitors_markup_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10,
        verbose_name="Monitors ustama (%)",
    )
    printers_markup_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10,
        verbose_name="Printers ustama (%)",
    )
    laptops_markup_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=10,
        verbose_name="Laptops ustama (%)",
    )
    max_discount_percent = models.PositiveSmallIntegerField(
        default=7,
        verbose_name="Maksimal chegirma (%)",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AIO Calculator Settings"
        verbose_name_plural = "AIO Calculator Settings"

    def __str__(self):
        return (
            f"Dollar kursi: {self.usd_rate} | "
            f"Ustama: {self.markup_percent}% | "
            f"Chegirma: 0–{self.max_discount_percent}%"
        )

    @classmethod
    def get_singleton(cls):
        obj, _ = cls.objects.get_or_create(
            pk=1,
            defaults={
                "usd_rate": 0,
                "markup_percent": 10,
                "branded_aio_markup_percent": 10,
                "branded_pc_markup_percent": 10,
                "monitors_markup_percent": 10,
                "printers_markup_percent": 10,
                "laptops_markup_percent": 10,
                "max_discount_percent": 7,
            },
        )
        return obj

    def get_markup_for(self, section="aio"):
        """section: 'aio' | 'branded_aio' | 'branded_pc' | 'monitors' | 'printers' | 'laptops'"""
        mapping = {
            "aio": self.markup_percent,
            "branded_aio": self.branded_aio_markup_percent,
            "branded_pc": self.branded_pc_markup_percent,
            "monitors": self.monitors_markup_percent,
            "printers": self.printers_markup_percent,
            "laptops": self.laptops_markup_percent,
        }
        return mapping.get(section, self.markup_percent)

    def effective_markup_percent(self, discount_percent=0, section="aio"):
        from decimal import Decimal

        base = Decimal(str(self.get_markup_for(section)))
        discount = min(
            max(Decimal("0"), Decimal(str(discount_percent))),
            Decimal(str(self.max_discount_percent)),
        )
        return base - discount

    def apply_markup(self, subtotal, discount_percent=0, section="aio"):
        from decimal import Decimal

        markup = self.effective_markup_percent(discount_percent, section)
        return subtotal * (Decimal("1") + markup / Decimal("100"))


class BuildQuote(models.Model):
    order_number = models.CharField(
        max_length=24,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Zakaz raqami",
    )
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
        verbose_name = "AIO Calculation"
        verbose_name_plural = "AIO Calculations"

    def __str__(self):
        label = self.order_number or f"AIO#{self.pk}"
        return f"{label} - {self.monoblock_base} - {self.total_price}"
