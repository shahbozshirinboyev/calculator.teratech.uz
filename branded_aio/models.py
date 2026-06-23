from django.db import models


class BrandedAio(models.Model):
    name = models.CharField(max_length=512)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["price", "name"]
        verbose_name = "Branded AIO"
        verbose_name_plural = "Branded AIOs"

    def __str__(self):
        return self.name
