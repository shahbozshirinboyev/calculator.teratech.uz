from django.contrib import admin

from .models import BuildQuote, CalculatorSettings


@admin.register(CalculatorSettings)
class CalculatorSettingsAdmin(admin.ModelAdmin):
    list_display = ("usd_rate", "updated_at")

    def has_add_permission(self, request):
        return not CalculatorSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BuildQuote)
class BuildQuoteAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "monoblock_base",
        "cpu",
        "subtotal_price",
        "markup_amount",
        "total_price",
        "total_price_uzs",
    )
    list_filter = ("created_at", "monoblock_base")
    search_fields = ("monoblock_base__name", "cpu__name")
    readonly_fields = (
        "created_at",
        "subtotal_price",
        "discount_percent",
        "markup_percent",
        "markup_amount",
        "usd_rate",
        "total_price",
        "total_price_uzs",
    )
    fieldsets = (
        (
            "Komponentlar",
            {
                "fields": (
                    "monoblock_base",
                    "cpu",
                    "ram_items",
                    "storage_items",
                    "keyboard_mouse",
                ),
            },
        ),
        (
            "Narx tafsilotlari",
            {
                "fields": (
                    "subtotal_price",
                    "discount_percent",
                    "markup_percent",
                    "markup_amount",
                    "usd_rate",
                    "total_price",
                    "total_price_uzs",
                ),
            },
        ),
        ("Vaqt", {"fields": ("created_at",)}),
    )

    @admin.display(description="Components")
    def components(self, obj):
        rams = ", ".join(item["name"] for item in obj.ram_items) or "No RAM"
        storages = ", ".join(item["name"] for item in obj.storage_items) or "No storage"
        return f"{rams} | {storages}"
