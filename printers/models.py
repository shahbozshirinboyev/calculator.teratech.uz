from django.db import models


class Printer(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["price", "name"]
        verbose_name = "Printer"
        verbose_name_plural = "Printers"

    def __str__(self):
        return self.name
