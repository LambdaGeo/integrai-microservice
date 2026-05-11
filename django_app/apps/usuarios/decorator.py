from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def login_required_message(function=None, redirect_field_name='next', login_url='login'):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, 'Você precisa estar logado para acessar esta página.')
                return redirect(login_url)
            return view_func(request, *args, **kwargs)

        return _wrapped_view

    if function:
        return decorator(function)
    return decorator
