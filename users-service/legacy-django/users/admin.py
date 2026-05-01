from django.contrib import admin
from .models import Usuario, AgenteProfile


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email')
    list_filter = ('is_active', 'is_staff')


@admin.register(AgenteProfile)
class AgenteProfileAdmin(admin.ModelAdmin):
    list_display = ('nome', 'area', 'ubs', 'user')
    search_fields = ('nome', 'area', 'ubs')