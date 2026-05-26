from decimal import Decimal

from django.core.management.base import BaseCommand

from products.models import CPU, MemoryType, MonoblockBase


class Command(BaseCommand):
    help = "Create standard monoblock base variants."

    BASES = [
        (24, "H61", MemoryType.DDR3, False),
        (27, "H61", MemoryType.DDR3, False),
        (24, "H610", MemoryType.DDR4, True),
        (27, "H610", MemoryType.DDR4, True),
        (32, "H610", MemoryType.DDR4, True),
        (24, "H610", MemoryType.DDR5, True),
        (27, "H610", MemoryType.DDR5, True),
        (32, "H610", MemoryType.DDR5, True),
    ]

    def handle(self, *args, **options):
        created = 0
        for size, chipset, ram_type, supports_nvme in self.BASES:
            name = f'{size}" FLAT IPS {chipset} {ram_type.upper()}'
            base, was_created = MonoblockBase.objects.get_or_create(
                name=name,
                motherboard_type=chipset,
                ram_type=ram_type,
                defaults={
                    "price": Decimal("0.00"),
                    "supports_nvme": supports_nvme,
                    "ram_slots": 2,
                    "supports_sata": True,
                    "is_active": True,
                },
            )
            cpus = CPU.objects.filter(compatible_bases__motherboard_type=chipset).distinct()
            if cpus.exists():
                base.cpus.add(*cpus)
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Created {created} monoblock base variants."))
