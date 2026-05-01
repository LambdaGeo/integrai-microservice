from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UsuarioManager(BaseUserManager):
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError("O CPF (username) é obrigatório.")
        username = ''.join(filter(str.isdigit, username))
        user = self.model(
            username=username,
            email=self.normalize_email(email),
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusuário precisa de is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusuário precisa de is_superuser=True")
        return self.create_user(username, email, password, **extra_fields)


class Usuario(AbstractUser):
    first_name = None
    last_name = None
    username = models.CharField(max_length=11, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]
    objects = UsuarioManager()

    def save(self, *args, **kwargs):
        if self.username:
            self.username = ''.join(filter(str.isdigit, self.username))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class AgenteProfile(models.Model):
    user = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name="profile"
    )
    nome = models.CharField(max_length=150)
    foto = models.ImageField(upload_to="fotos_agentes/", blank=True, null=True)
    area = models.CharField(max_length=100)
    ubs = models.CharField(max_length=100)

    @property
    def primeiro_nome(self):
        return self.nome.split()[0] if self.nome else ""

    def __str__(self):
        return self.nome or self.user.username