from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.templatetags.static import static
from datetime import date
import re
import os
import uuid


class Gestante(models.Model):
    VULNERABILIDADE = [
        (True, 'Sim'),
        (False, 'Não'),
    ]

    nome = models.CharField(max_length=100, verbose_name="Nome Completo")
    data_nascimento = models.DateField(verbose_name="Data de Nascimento", blank=False, null=False)
    peso = models.PositiveIntegerField(verbose_name="Peso pré-gestacional (kg)", blank=False, null=False)
    altura = models.FloatField(verbose_name="Altura (m)", blank=False, null=False)
    telefone = models.CharField(max_length=20, verbose_name="Telefone", blank=True)
    vulnerabilidade_social = models.BooleanField(default=False, choices=VULNERABILIDADE, blank=True, verbose_name='Vulnerabilidade social?')
    foto = models.ImageField(upload_to='foto_upload_path', blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=False, related_name='gestantes', verbose_name="Agente responsável")

    def foto_upload_path(instance, filename):
        base, ext = os.path.splitext(filename)
        nome = instance.nome.replace(" ", "_") if instance.nome else "gestante"
        identificador = instance.id or uuid.uuid4().hex[:8]
        return f"fotos/{nome}_{identificador}/{filename}"

    @property
    def foto_url(self):
        if self.foto and hasattr(self.foto, 'url'):
            return self.foto.url
        return static('assets/imagens/gestante/silhueta.png')

    @property
    def imc(self):
        if self.altura > 0:
            return round(self.peso / (self.altura ** 2), 2)
        return None

    @property
    def imc_classificacao(self):
        imc = self.imc
        if imc is None:
            return "Altura ou peso inválidos"
        if imc < 18.5:
            return "Baixo peso"
        elif 18.5 <= imc <= 24.9:
            return "Adequado"
        else:
            return "Excesso de peso"

    @property
    def telefone_whatsapp(self):
        if not self.telefone:
            return None
        return re.sub(r'\D', '', self.telefone)

    @property
    def idade(self):
        today = date.today()
        return today.year - self.data_nascimento.year - ((today.month, today.day) < (self.data_nascimento.month, self.data_nascimento.day))

    def clean(self):
        if self.peso < 30 or self.peso > 200:
            raise ValidationError("O peso deve estar entre 30 e 200 kg.")
        if self.idade < 10 or self.idade > 60:
            raise ValidationError("A idade deve estar entre 10 e 60 anos.")
        if self.altura < 1.0 or self.altura > 2.5:
            raise ValidationError("A altura deve estar entre 1.0 e 2.5 metros.")

    def __str__(self):
        return f"{self.nome} (ID: {self.id})"

    class Meta:
        ordering = ['-data_cadastro']
        verbose_name = "Gestante"
        verbose_name_plural = "Gestantes"


class ConsentimentoGestante(models.Model):
    gestante = models.ForeignKey('Gestante', on_delete=models.CASCADE, related_name='consentimentos')
    usuario = models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Registrado por")
    data_registro = models.DateTimeField(auto_now_add=True)
    STATUS_CONSENTIMENTO = [('aceito', 'Aceito'), ('revogado', 'Revogado')]
    status = models.CharField(max_length=10, choices=STATUS_CONSENTIMENTO)
    motivo_revogacao = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-data_registro']

    def __str__(self):
        return f"{self.gestante.nome} - {self.status} em {self.data_registro.strftime('%d/%m/%Y %H:%M')}"