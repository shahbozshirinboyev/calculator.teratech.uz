from django.contrib import admin

from .models import BuildQuote, CalculatorSettings


@admin.register(CalculatorSettings)
class CalculatorSettingsAdmin(admin.ModelAdmin):
    list_display = (
        "usd_rate", "markup_percent", "monitors_markup_percent",
        "printers_markup_percent", "max_discount_percent", "updated_at",
    )
    fieldsets = (
        ("Umumiy", {
            "fields": ("usd_rate", "max_discount_percent"),
        }),
        ("Ustama foizlari (%)", {
            "fields": (
                "markup_percent",
                "monitors_markup_percent",
                "printers_markup_percent",
            ),
        }),
    )

    def has_add_permission(self, request):
        return not CalculatorSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(BuildQuote)
class BuildQuoteAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "monoblock_base_summary",
        "created_at",
    )
    list_filter = ("created_at", "monoblock_base")
    search_fields = ("order_number", "monoblock_base__name", "cpu__name")
    readonly_fields = (
        "order_number",
        "created_at",
        "components_table",
        "price_details_inline",
    )
    fieldsets = (
        (
            "Komponentlar",
            {
                "fields": ("components_table",),
            },
        ),
        (
            "Narx tafsilotlari",
            {
                "fields": ("price_details_inline",),
            },
        ),
        ("Vaqt", {"fields": ("created_at",)}),
    )

    @admin.display(description="")
    def components_table(self, obj):
        from django.utils.html import format_html
        
        # RAM items
        ram_text = self.format_items(obj.ram_items, "RAM tanlanmagan")
        
        # Storage items
        storage_text = self.format_items(obj.storage_items, "Storage tanlanmagan")
        
        # AIO
        aio_text = f"{obj.monoblock_base.name} (${obj.monoblock_base.price})" if obj.monoblock_base else "AIO tanlanmagan"
        
        # CPU
        cpu_text = f"{obj.cpu.name} (${obj.cpu.price})" if obj.cpu else "CPU tanlanmagan"
        
        # Keyboard Mouse
        km_text = f"{obj.keyboard_mouse.name} (${obj.keyboard_mouse.price})" if obj.keyboard_mouse else "Keyboard/Mouse tanlanmagan"
        
        html = """
        <style>
            .form-row.field-components_table label {{{{
                display: none !important;
            }}}}
            .form-row.field-components_table .readonly {{{{
                margin-left: 0 !important;
            }}}}
        </style>
        <table style="width: 100%; table-layout: fixed;">
            <tr>
                <th>AIO</th>
                <th>CPU</th>
                <th>RAM</th>
                <th>Storage</th>
                <th>Keyboard and Mouse</th>
            </tr>
            <tr>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
            </tr>
        </table>
        """.format(aio_text, cpu_text, ram_text, storage_text, km_text)
        
        return format_html(html)

    @admin.display(description="AIO")
    def monoblock_base_summary(self, obj):
        if not obj.monoblock_base:
            return "AIO tanlanmagan"
        return f"{obj.monoblock_base.name} (${obj.monoblock_base.price})"

    @admin.display(description="CPU")
    def cpu_summary(self, obj):
        if not obj.cpu:
            return "CPU tanlanmagan"
        return f"{obj.cpu.name} (${obj.cpu.price})"

    @admin.display(description="RAM")
    def ram_summary(self, obj):
        return self.format_items(obj.ram_items, "RAM tanlanmagan")

    @admin.display(description="Storage")
    def storage_summary(self, obj):
        return self.format_items(obj.storage_items, "Storage tanlanmagan")

    @admin.display(description="Keyboard and Mouse")
    def keyboard_mouse_summary(self, obj):
        if not obj.keyboard_mouse:
            return "Keyboard/Mouse tanlanmagan"
        return f"{obj.keyboard_mouse.name} (${obj.keyboard_mouse.price})"

    @admin.display(description="")
    def price_details_inline(self, obj):
        from django.utils.html import format_html
        
        html = """
        <style>
            .form-row.field-price_details_inline label {{{{
                display: none !important;
            }}}}
            .form-row.field-price_details_inline .readonly {{{{
                margin-left: 0 !important;
            }}}}
        </style>
        <table style="width: 100%; table-layout: fixed;">
            <tr>
                <th>Jami (USD)</th>
                <th>Sof narx (USD)</th>
                <th>Ustama summasi (USD)</th>
                <th>Ustama (%)</th>
                <th>Dollar kursi (so'm)</th>
            </tr>
            <tr>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
            </tr>
        </table>
        """.format(
            obj.total_price,
            obj.subtotal_price,
            obj.markup_amount,
            obj.markup_percent,
            obj.usd_rate
        )
        
        return format_html(html)

    def format_items(self, items, empty_text):
        if not items:
            return empty_text
        return ", ".join(
            f"{item.get('name', '-')} (${item.get('price', '0')})"
            for item in items
        )
