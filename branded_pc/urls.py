from django.urls import path

from . import views

app_name = "branded_pc"

urlpatterns = [
    path("", views.branded_pc_list, name="list"),
]
