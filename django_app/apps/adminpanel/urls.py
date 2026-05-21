from django.urls import path

from . import views


app_name = "custom_admin"

urlpatterns = [
    path("", views.dashboard, name="index"),
    path("usuarios/<int:usuario_id>/<str:action>/", views.usuario_action, name="usuario_action"),
    path("gestantes/<int:gestante_id>/delete/", views.delete_gestante, name="delete_gestante"),
    path("gestantes/<int:gestante_id>/consentimento/<str:status>/", views.set_consentimento, name="set_consentimento"),
    path("avaliacoes/<int:avaliacao_id>/delete/", views.delete_avaliacao, name="delete_avaliacao"),
    path("pilulas/<int:pilula_id>/enviar/", views.mark_pilula_sent, name="mark_pilula_sent"),
    path("pilulas/<int:pilula_id>/delete/", views.delete_pilula, name="delete_pilula"),
]
