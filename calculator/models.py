from django.db import models

from products.models import CPU, KeyboardMouse, MonoblockBase


class CalculatorSettings(models.Model):
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
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Saved Calculation"
        verbose_name_plural = "Saved Calculations"

    def __str__(self):
        return f"{self.monoblock_base} - {self.total_price}"
