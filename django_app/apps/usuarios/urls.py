from django.urls import path

from apps.usuarios.views import login, cadastro, logout, editar_perfil, meu_perfil

urlpatterns = [
    path('login/', login, name='login'),
    path('cadastro/', cadastro, name='cadastro'),
    path('logout/', logout, name='logout'),
    path("perfil/editar/", editar_perfil, name="editar_perfil"),
    path("perfil/", meu_perfil, name="meu_perfil"),
]