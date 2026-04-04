from django.urls import path
from . import views

app_name = "inventory"

urlpatterns = [
    path("ping/<str:ip>/", views.ping_ip, name="ping_ip"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("relatorio/geral/", views.relatorio_geral, name="relatorio_geral"),
]
