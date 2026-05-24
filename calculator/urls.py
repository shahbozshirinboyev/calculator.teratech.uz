from django.urls import path

from . import views

app_name = "calculator"

urlpatterns = [
    path("", views.calculator, name="home"),
    path("quotes/save/", views.save_quote, name="save_quote"),
]
