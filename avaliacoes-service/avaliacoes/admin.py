from django.contrib import admin
from .models import Avaliacao, Pilula


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ('gestante', 'data_aplicacao', 'status_processamento_llm', 'status_processamento_pills')
    list_filter = ('status_processamento_llm', 'status_processamento_pills', 'data_aplicacao')


@admin.register(Pilula)
class PilulaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'avaliacao', 'semana_num', 'status', 'data_envio')
    list_filter = ('status',)
    search_fields = ('titulo',)