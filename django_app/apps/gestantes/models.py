"""
Modelos de Gestantes - LEGACY
==============================
ATENÇÃO: Estes modelos foram migrados para o microservice gestantes-service.
O Django agora usa autenticação via API e não persiste mais dados localmente.

Os dados são armazenados no microservice gestantes-service.
Para criar/editar gestantes, use a API do microservice:
- POST /api/v1/gestantes - criar gestante
- PUT /api/v1/gestantes/{id} - atualizar gestante
- GET /api/v1/gestantes - listar gestantes

Consentimentos são gerenciados via:
- POST /api/v1/consentimentos - criar consentimento
- GET /api/v1/consentimentos - listar consentimentos

Mantenemos este arquivo apenas para compatibilidade com código legado
e para superusários administrativos que precisam de acesso ao admin Django.
"""

# # ==========================
# # Modelos Legados - DESABILITADOS
# # ==========================
# # Todos os modelos abaixo foram movidos para o microservice gestantes-service
# # e estão comentados para evitar conflitos com a API central.
# # Para adicionar novos modelos, use o microservice ao invés do Django local.
# #
# # Modelos desabilitados:
# # - Gestante
# # - ConsentimentoGestante
# # - Avaliacao
# # - Pilula
