from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, AgenteProfile  # <-- usa o Custom User!

# --- Customização de Títulos (Seu código) ---
admin.site.site_header = "IntegrAI Administração"
admin.site.site_title = "IntegrAI"
admin.site.index_title = "Painel de Gestão"


# --- Inline para o Profile ---
class AgenteProfileInline(admin.StackedInline):
    model = AgenteProfile
    can_delete = False
    verbose_name_plural = "Perfil do Agente"
    fk_name = "user"


# --- Admin Customizado para o Usuário (CPF) ---
@admin.register(Usuario)
class CustomUserAdmin(UserAdmin):
    inlines = (AgenteProfileInline,)

    list_display = ("username", "email", "get_nome_completo", "is_staff")

    @admin.display(description="Nome Completo")
    def get_nome_completo(self, obj):
        return getattr(obj.profile, "nome", "")

    # Campos exibidos na edição de usuário
    fieldsets = (
        (None, {"fields": ("username", "password")}),  # username = CPF
        ("Informações pessoais", {"fields": ("first_name", "last_name", "email")}),
        ("Permissões", {
            "fields": (
                "is_active",
                "is_staff",
                "is_superuser",
                "groups",
                "user_permissions",
            )
        }),
        ("Datas importantes", {"fields": ("last_login", "date_joined")}),
    )

    # Campos exibidos ao criar um usuário no Admin
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2"),
        }),
    )