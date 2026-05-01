"""
Modelos de Usuário - LEGACY
===========================
ATENÇÃO: Estes modelos foram migrados para o microservice users-service.
O Django agora usa autenticação via API e não persiste mais dados localmente.

Os dados são armazenados na sessão do Django após login bem-sucedido.
Para criar/editar usuários, use a API do microservice:
- POST /api/v1/usuarios - criar usuário
- PUT /api/v1/usuarios/{id} - atualizar usuário
- GET /api/v1/usuarios/profile/me - obter perfil do agente

Mantenemos estes modelos apenas para compatibilidade com código legado
e para superusários administrativos que precisam de acesso ao admin Django.
"""

"""
Módulo de usuários migrado para o microservice users-service.
O Django frontend não persiste mais dados de usuário localmente.
A autenticação é realizada via API REST pelo MicroserviceBackend.
"""
# from django.db import models
# from django.contrib.auth.models import AbstractUser, BaseUserManager
# import warnings


# # ==========================
# #  Custom Manager
# # ==========================
# class UsuarioManager(BaseUserManager):

#     def create_user(self, username, email=None, password=None, **extra_fields):
#         warnings.warn(
#             "Usuario local foi migrado para microservice. "
#             "Use a API users-service para criar usuários.",
#             DeprecationWarning
#         )
#         if not username:
#             raise ValueError("O CPF (username) é obrigatório.")

#         username = ''.join(filter(str.isdigit, username))  # só números

#         user = self.model(
#             username=username,
#             email=self.normalize_email(email),
#             **extra_fields
#         )

#         user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_superuser(self, username, email=None, password=None, **extra_fields):
#         extra_fields.setdefault("is_staff", True)
#         extra_fields.setdefault("is_superuser", True)
#         extra_fields.setdefault("is_active", True)

#         if extra_fields.get("is_staff") is not True:
#             raise ValueError("Superusuário precisa de is_staff=True")

#         if extra_fields.get("is_superuser") is not True:
#             raise ValueError("Superusuário precisa de is_superuser=True")

#         return self.create_user(username, email, password, **extra_fields)


# # ==========================
# #  Usuário personalizado
# # ==========================
# class Usuario(AbstractUser):
#     """
#     Modelo legacy - migrado para microservice.
#     Mantido apenas para superusários admin e compatibilidade.
#     """
#     # Remover campos herdados que não queremos usar:
#     first_name = None
#     last_name = None

#     # CPF será o login
#     username = models.CharField(max_length=11, unique=True)
#     email = models.EmailField(unique=True, null=True, blank=True)

#     USERNAME_FIELD = "username"   # login = CPF
#     REQUIRED_FIELDS = ["email"]

#     objects = UsuarioManager()  # <<< ESSENCIAL >>>

#     def save(self, *args, **kwargs):
#         warnings.warn(
#             "Usuario local foi migrado para microservice. "
#             "Use a API users-service para gerenciar usuários.",
#             DeprecationWarning
#         )
#         if self.username:
#             self.username = ''.join(filter(str.isdigit, self.username))
#         super().save(*args, **kwargs)

#     def __str__(self):
#         return self.username


# # ==========================
# #  Profile do Agente (LEGACY)
# # ==========================
# class AgenteProfile(models.Model):
#     """
#     Modelo legacy - migrado para microservice users-service.
#     O perfil do agente agora é gerenciado via API.
    
#     Mantido apenas para compatibilidade com código existente.
#     """
#     user = models.OneToOneField(
#         Usuario,
#         on_delete=models.CASCADE,
#         related_name="profile"
#     )

#     nome = models.CharField(max_length=150)
#     foto = models.ImageField(upload_to="fotos_agentes/", blank=True, null=True)
#     area = models.CharField(max_length=100)
#     UBS = models.CharField(max_length=100)

#     @property
#     def primeiro_nome(self):
#         return self.nome.split()[0]

#     def __str__(self):
#         return self.nome or self.user.username
