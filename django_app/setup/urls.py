"""
URL configuration for setup project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path

from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve as static_serve

from django.contrib.auth import views as auth_views

urlpatterns = [
        #path('admin/', admin.site.urls, name='admin'),
        path('', include('apps.gestantes.urls')),
        path('', include('apps.usuarios.urls')),
        path('django-rq/', include('django_rq.urls')),
        
        # Password reset desabilitado - usar microservice
        # path('senha/reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
        # path('senha/reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
        # path('senha/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
        # path('senha/reset/complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

        path("senha/alterar/", auth_views.PasswordChangeView.as_view(template_name="usuarios/alterar_senha.html"), name="password_change"),
        path("senha/alterar/sucesso/", auth_views.PasswordChangeDoneView.as_view(template_name="usuarios/senha_alterada.html"), name="password_change_done"),

]

if settings.DEBUG:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
        urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
        urlpatterns += [
                re_path(r'^static/(?P<path>.*)$', static_serve, {'document_root': settings.STATIC_ROOT}),
        ]
