from django.contrib import admin

from .models import CPU, RAM, KeyboardMouse, MonoblockBase, Storage


@admin.register(MonoblockBase)
class MonoblockBaseAdmin(admin.ModelAdmin):
    ordering = ("price", "name")

    class Media:
        css = {"all": ("products/admin.css",)}

    list_display = (
        "name",
        "price",
        "motherboard_type",
        "ram_type",
        "supports_sata",
        "supports_nvme",
        "is_active",
    )
    list_editable = ("price", "is_active")
    fields = (
        "name",
        "price",
        "motherboard_type",
        "ram_type",
        "supports_sata",
        "supports_nvme",
        "is_active",
    )
    list_filter = ("motherboard_type", "ram_type", "supports_sata", "supports_nvme", "is_active")
    search_fields = ("name",)


@admin.register(CPU)
class CPUAdmin(admin.ModelAdmin):
    ordering = ("price", "name")

    list_display = ("name", "price", "compatible", "is_active")
    list_editable = ("price", "is_active")
    fields = ("name", "price", "compatible_bases", "is_active")
    list_filter = ("compatible_bases", "is_active")
    search_fields = ("name",)
    filter_horizontal = ("compatible_bases",)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("compatible_bases")

    @admin.display(description="Compatible")
    def compatible(self, obj):
        return ", ".join(obj.compatible_bases.values_list("name", flat=True)) or "-"


@admin.register(RAM)
class RAMAdmin(admin.ModelAdmin):
    ordering = ("price", "name")

    list_display = ("name", "price", "ram_type", "capacity_gb",  "is_active")
    list_editable = ("price", "is_active")
    fields = ("name", "price", "ram_type", "capacity_gb", "is_active")
    list_filter = ("ram_type", "is_active")
    search_fields = ("name",)


@admin.register(Storage)
class StorageAdmin(admin.ModelAdmin):
    ordering = ("price", "name")

    list_display = ("name", "price", "kind", "interface", "capacity_gb", "is_active")
    list_editable = ("price", "is_active")
    fields = ("name", "price", "kind", "interface", "capacity_gb", "is_active")
    list_filter = ("kind", "interface", "is_active")
    search_fields = ("name",)


@admin.register(KeyboardMouse)
class KeyboardMouseAdmin(admin.ModelAdmin):
    ordering = ("price", "name")

    list_display = ("name", "price", "is_active")
    list_editable = ("price", "is_active")
    fields = ("name", "price", "is_active")
    search_fields = ("name",)


_original_get_app_list = admin.site.get_app_list
_products_order = {
    "AIOs": 0,
    "CPUs": 1,
    "RAMs": 2,
    "Storages": 3,
    "Keyboard and Mouse": 4,
}

_app_order = {
    "auth": 0,
    "calculator": 1,
    "products": 2,
    "monitors": 3,
    "printers": 4,
    "laptops": 5,
    "orders": 6,
}


def get_app_list(request, app_label=None):
    app_list = _original_get_app_list(request, app_label)
    for app in app_list:
        if app["app_label"] == "products":
            app["models"].sort(key=lambda model: _products_order.get(model["name"], 99))
    app_list.sort(key=lambda app: _app_order.get(app["app_label"], 99))
    return app_list


admin.site.get_app_list = get_app_list
