from django.urls import path

from . import views

app_name = "branded_aio"

urlpatterns = [
    path("", views.branded_aio_list, name="list"),
]
