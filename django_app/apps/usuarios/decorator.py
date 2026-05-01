from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages

def login_required_message(function=None, redirect_field_name='next', login_url='login/'):
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Você precisa estar logado para acessar esta página.')
            return actual_decorator(view_func)(request, *args, **kwargs)
        return _wrapped_view
    if function:
        return decorator(function)
    return decorator
