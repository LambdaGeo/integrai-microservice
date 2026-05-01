from django.conf import settings

def global_variables(request):
    return {
        'CHAINLIT_URL': settings.CHAINLIT_URL,
    }