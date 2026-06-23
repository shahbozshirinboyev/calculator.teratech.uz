from django.contrib import admin

from .models import BrandedAio


@admin.register(BrandedAio)
class BrandedAioAdmin(admin.ModelAdmin):
    ordering = ("price", "name")
    list_display = ("name", "price", "is_active")
    list_editable = ("price", "is_active")
    fields = ("name", "price", "is_active")
    search_fields = ("name",)
    list_filter = ("is_active",)
