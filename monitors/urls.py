from django.urls import path

from . import views

app_name = "monitors"

urlpatterns = [
    path("", views.monitor_list, name="list"),
    path("save/", views.save_monitor_quote, name="save_quote"),
]
