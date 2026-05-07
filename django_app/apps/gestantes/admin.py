from django.contrib import admin

from datetime import timedelta

# DESABILITADO: Modelos migrados para microservice gestantes-service
# from apps.gestantes.models import Gestante, Avaliacao, ConsentimentoGestante, Pilula


admin.site.site_header = "Administrador do Site"  # Título do cabeçalho
admin.site.site_title = "Administração do Meu Site"  # Título na aba do navegador
admin.site.index_title = "Bem-vindo ao Painel de Controle"  # Título na página inicial do admin


class ListandoGestante(admin.ModelAdmin):
    #list_display = ("id", "nome", "sexo", "idade","foto")
    list_display = ("id", "nome", "idade","foto")
    list_display_links = ("id","nome")
    search_fields = ("nome",)
    #list_filter = ("sexo",)
    list_editable = ( "foto", )
    #list_editable = ("sexo","idade", "foto")
    list_per_page = 10

admin.site.register(Gestante, ListandoGestante)


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ('id', 'gestante', 'data_aplicacao', 'peso_atual')
    search_fields = ('gestante__nome', 'peso_atual')
    list_filter = ('data_aplicacao',)

@admin.register(ConsentimentoGestante)
class ConsentimentoGestanteAdmin(admin.ModelAdmin):
    list_display = ('gestante', 'status', 'usuario', 'data_registro')
    list_filter = ('status', 'data_registro')
    search_fields = ('gestante__nome', 'usuario__username')


from django.contrib import admin
from .models import Pilula

@admin.register(Pilula)
class PilulaAdmin(admin.ModelAdmin):
    list_display = (
        'titulo',
        'avaliacao',
        'semana_ord_display',
        'periodo_envio_display',
        'status',
        'data_geracao',
        'data_envio',
    )
    list_filter = ('status', 'avaliacao')
    search_fields = ('titulo', 'conteudo')
    #readonly_fields = ('data_geracao', 'data_envio')

    def semana_ord_display(self, obj):
        """Exibe o número da semana formatado (ex: 1ª, 2ª...)."""
        return obj.semana_ord or "-"
    semana_ord_display.short_description = "Semana"

    def periodo_envio_display(self, obj):
        """Exibe o intervalo de envio formatado (ex: 1 a 7 de outubro)."""
        return obj.periodo_envio or "-"
    periodo_envio_display.short_description = "Período de Envio"
