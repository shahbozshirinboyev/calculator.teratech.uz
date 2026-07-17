from django.urls import path

from . import views

app_name = "orders"

urlpatterns = [
    path("", views.order_list, name="list"),
    path("create/", views.order_create, name="create"),
    path("<int:pk>/", views.order_detail, name="detail"),
    path("<int:pk>/status/", views.order_update_status, name="update_status"),
    path("leaderboard/", views.leaderboard, name="leaderboard"),
    path("profile/", views.seller_profile, name="profile"),
]
