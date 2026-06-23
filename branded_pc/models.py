from django.db import models


class BrandedPc(models.Model):
    name = models.CharField(max_length=512)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["price", "name"]
        verbose_name = "Branded PC"
        verbose_name_plural = "Branded PCs"

    def __str__(self):
        return self.name
