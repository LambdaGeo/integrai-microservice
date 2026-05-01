from django.contrib import admin
from .models import Gestante, ConsentimentoGestante


@admin.register(Gestante)
class GestanteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'telefone', 'data_nascimento', 'usuario', 'data_cadastro')
    search_fields = ('nome', 'telefone')
    list_filter = ('data_cadastro', 'vulnerabilidade_social')


@admin.register(ConsentimentoGestante)
class ConsentimentoGestanteAdmin(admin.ModelAdmin):
    list_display = ('gestante', 'status', 'data_registro')
    list_filter = ('status',)