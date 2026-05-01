from django.apps import AppConfig


class GestantesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.gestantes'

    def ready(self):
        """
        Esta função é chamada quando o app está pronto.
        É o local correto para importar e registrar os sinais.
        """
        # Importa os sinais (que estão dentro do models.py)
        import apps.gestantes.models

