from django.contrib import admin

from .models import BuildQuote, CalculatorSettings


@admin.register(CalculatorSettings)
class CalculatorSettingsAdmin(admin.ModelAdmin):
    list_display = ("usd_rate", "markup_percent", "max_discount_percent", "updated_at")
    fields = ("usd_rate", "markup_percent", "max_discount_percent")

    def has_add_permission(self, request):
        return not CalculatorSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BuildQuote)
class BuildQuoteAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "created_at",
        "monoblock_base",
        "cpu",
        "ram_summary",
        "storage_summary",
        "subtotal_price",
        "markup_amount",
        "total_price",
        "total_price_uzs",
    )
    list_filter = ("created_at", "monoblock_base")
    search_fields = ("order_number", "monoblock_base__name", "cpu__name")
    readonly_fields = (
        "order_number",
        "created_at",
        "ram_summary",
        "storage_summary",
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
                    "order_number",
                    "monoblock_base",
                    "cpu",
                    "ram_summary",
                    "storage_summary",
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

    @admin.display(description="RAM")
    def ram_summary(self, obj):
        return self.format_items(obj.ram_items, "RAM tanlanmagan")

    @admin.display(description="Storage")
    def storage_summary(self, obj):
        return self.format_items(obj.storage_items, "Storage tanlanmagan")

    def format_items(self, items, empty_text):
        if not items:
            return empty_text
        return ", ".join(
            f"{item.get('name', '-')} (${item.get('price', '0')})"
            for item in items
        )
