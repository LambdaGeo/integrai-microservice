from django.urls import path

# Importa os módulos de view separados em vez de um único arquivo
#from apps.gestantes.views import core_views, gestante_views, avaliacao_views, comunicacao_views
from .views import core_views, gestante_views, avaliacao_views, comunicacao_views


urlpatterns = [
    # ===================================
    # Padrões de Core (core_views.py) e Gestante (gestante_views.py)
    # ===================================
    # A sua view 'index' (que lista as gestantes) é a raiz
    path('', gestante_views.index, name='index'), 
    
    # A sua view 'home' (página pública)
    path('home', core_views.home, name='home'),
    
    # A sua view 'chat'
    path('chat', core_views.chat, name='chat'),

    # ===================================
    # Padrões de Comunicação (comunicacao_views.py e views_fake.py)
    # ===================================
    path('comunica/<int:gestante_id>', comunicacao_views.comunica, name='comunica'),
    path('pilulas/<int:gestante_id>', comunicacao_views.pilulas, name='pilulas'),
    path('pilula/<int:pilula_id>/status/', comunicacao_views.atualizar_status_pilula, name='atualizar_status_pilula'),

    path("gestantes/<int:gestante_id>/resumo/", comunicacao_views.resumo_riscos_api, name="resumo_riscos_api"),

    # ===================================
    # Padrões de Avaliação (avaliacao_views.py)
    # ===================================
    path('gestante/<int:gestante_id>/', avaliacao_views.gestante, name='gestante'),
    path('gestante/<int:gestante_id>/cadastrar_questionario/', avaliacao_views.avaliacao, name='questionario'),
    path('avaliacao-status/<int:gestante_id>/', avaliacao_views.avaliacao_status, name='avaliacao_status'),

    path("api-predicao-status/", avaliacao_views.api_predicao_status, name="api_predicao_status"),

    # ===================================
    # Padrões de Gestante (gestante_views.py)
    # ===================================
    path('gestante/<int:gestante_id>/revogar_consentimento/', gestante_views.revogar_consentimento, 
         name='revogar_consentimento'),
    
    path ('buscar', gestante_views.buscar, name='buscar'),
    path('nova-gestante', gestante_views.nova_gestante, name='nova_gestante'),
    path('editar-gestante/<int:gestante_id>', gestante_views.editar_gestante, name='editar_gestante'),
    path('deletar-gestante/<int:gestante_id>', gestante_views.deletar_gestante, name='deletar_gestante'),
     
]