# Generated manually on 2026-05-26

from django.db import migrations, models


def copy_sata_support(apps, schema_editor):
    MonoblockBase = apps.get_model("products", "MonoblockBase")
    for base in MonoblockBase.objects.all():
        base.supports_sata = base.sata_ports > 0
        base.save(update_fields=["supports_sata"])


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0003_alter_monoblockbase_motherboard_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="monoblockbase",
            name="supports_sata",
            field=models.BooleanField(default=True),
        ),
        migrations.RunPython(copy_sata_support, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="monoblockbase",
            name="sata_ports",
        ),
    ]
