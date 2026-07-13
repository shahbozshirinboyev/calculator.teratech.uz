from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("config_label", "quantity", "unit_price_usd")
    readonly_fields = ("line_total_usd_display",)

    @admin.display(description="Jami (USD)")
    def line_total_usd_display(self, obj):
        return f"${obj.line_total_usd:.2f}"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number", "customer_name", "sold_by",
        "production_status", "payment_status",
        "total_price_usd", "created_at",
    )
    list_filter = ("production_status", "payment_status", "delivery_type", "sold_by")
    search_fields = ("order_number", "customer_name", "customer_phone")
    readonly_fields = ("order_number", "created_at", "updated_at", "delivered_at")
    inlines = [OrderItemInline]
    ordering = ("-created_at",)
