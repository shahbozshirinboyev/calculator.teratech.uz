from django.urls import path

from . import views

app_name = "laptops"

urlpatterns = [
    path("", views.laptop_list, name="list"),
    path("save/", views.save_laptop_quote, name="save_quote"),
]
