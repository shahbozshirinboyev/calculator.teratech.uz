from django.db import models


class MemoryType(models.TextChoices):
    DDR3 = "ddr3", "DDR3"
    DDR4 = "ddr4", "DDR4"
    DDR5 = "ddr5", "DDR5"


class StorageInterface(models.TextChoices):
    SATA = "sata", "SATA"
    NVME = "nvme", "NVMe"


class PricedItem(models.Model):
    name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class MonoblockBase(PricedItem):
    motherboard_type = models.CharField("MB Type", max_length=10)
    ram_type = models.CharField(max_length=10, choices=MemoryType.choices)
    ram_slots = models.PositiveSmallIntegerField(default=2)
    sata_ports = models.PositiveSmallIntegerField(default=1)
    supports_nvme = models.BooleanField(default=False)

    class Meta:
        ordering = ["motherboard_type", "ram_type", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["name", "motherboard_type", "ram_type"],
                name="unique_monoblock_base",
            )
        ]
        verbose_name = "AIO"
        verbose_name_plural = "AIOs"

    def __str__(self):
        return self.name


class CPU(PricedItem):
    compatible_bases = models.ManyToManyField(MonoblockBase, related_name="cpus")

    class Meta:
        ordering = ["name"]
        verbose_name = "CPU"
        verbose_name_plural = "CPUs"


class RAM(PricedItem):
    ram_type = models.CharField(max_length=10, choices=MemoryType.choices)
    capacity_gb = models.PositiveSmallIntegerField(blank=True, null=True)

    class Meta:
        ordering = ["ram_type", "capacity_gb", "name"]
        verbose_name = "RAM"
        verbose_name_plural = "RAMs"

    def __str__(self):
        return f"{self.name} ({self.get_ram_type_display()})"


class Storage(PricedItem):
    class Kind(models.TextChoices):
        SSD = "ssd", "SSD"
        HDD = "hdd", "HDD"

    kind = models.CharField(max_length=10, choices=Kind.choices)
    interface = models.CharField(max_length=10, choices=StorageInterface.choices)
    capacity_gb = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ["kind", "interface", "capacity_gb", "name"]
        verbose_name = "Storage"
        verbose_name_plural = "Storages"

    def __str__(self):
        return f"{self.name} ({self.get_kind_display()}, {self.get_interface_display()})"


class KeyboardMouse(PricedItem):
    class Meta:
        ordering = ["name"]
        verbose_name = "Keyboard and Mouse"
        verbose_name_plural = "Keyboard and Mouse"
