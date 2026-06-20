from django.urls import path

from . import views

app_name = "printers"

urlpatterns = [
    path("", views.printer_list, name="list"),
    path("save/", views.save_printer_quote, name="save_quote"),
]
