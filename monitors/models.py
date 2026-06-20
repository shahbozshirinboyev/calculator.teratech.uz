from django.db import models


class Monitor(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["price", "name"]
        verbose_name = "Monitor"
        verbose_name_plural = "Monitors"

    def __str__(self):
        return self.name
