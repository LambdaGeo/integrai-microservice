from django.db import models
from django import forms

from datetime import datetime

from django.utils import timezone

#from django.contrib.auth.models import User
from django.conf import settings

from django.core.exceptions import ValidationError

from django.contrib.postgres.fields import JSONField  # Se estiver usando PostgreSQL

from django.templatetags.static import static
from datetime import date
import locale

from datetime import timedelta

import uuid
import os

import re

class Gestante(models.Model):

    VULNERABILIDADE = [
        (True, 'Sim'),
        (False, 'Não'),
    ]

    nome = models.CharField(max_length=100, verbose_name="Nome Completo")
    
    data_nascimento = models.DateField(
        verbose_name="Data de Nascimento",
        blank=False,
        null=False
    )

    peso = models.PositiveIntegerField(
        verbose_name="Peso pré-gestacional (kg)",
        blank=False,
        null=False
    )
    altura = models.FloatField(
        verbose_name="Altura (m)",
        blank=False,
        null=False
    )

    telefone = models.CharField(
        max_length=20,
        verbose_name="Telefone (preferencialmente WhatsApp)",
        blank=True,
        help_text="Ex.: (83) 99999-1234"
    )

    vulnerabilidade_social = models.BooleanField(
        default=False, 
        choices=VULNERABILIDADE,
        blank=True,
        verbose_name='Com base nas suas visitas domiciliares, você considera essa gestante em condição de vulnerabilidade social?'
    )

    def foto_upload_path_apagar(instance, filename):
        return f'fotos/{instance.nome}_{instance.id}/{filename}'
    
    def foto_upload_path(instance, filename):
        base, ext = os.path.splitext(filename)
        nome = instance.nome.replace(" ", "_") if instance.nome else "gestante"
        identificador = instance.id or uuid.uuid4().hex[:8]
        return f"fotos/{nome}_{identificador}/{filename}"

    foto = models.ImageField(upload_to=foto_upload_path, blank=True)


    
    data_cadastro = models.DateTimeField(auto_now_add=True)

    usuario = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        related_name='gestantes',
        verbose_name="Agente responsável"
    )

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
    def imc_cor(self):
        """Retorna a cor Bootstrap correspondente à classificação do IMC."""
        classe = self.imc_classificacao

        if classe == "Baixo peso":
            return "text-warning"      # amarelo
        elif classe == "Adequado":
            return "text-success"      # verde
        elif classe == "Excesso de peso":
            return "text-danger"       # vermelho
        return "text-muted"
        
    @property
    def telefone_whatsapp(self):
        """
        Retorna o telefone apenas com dígitos, no padrão exigido pelo wa.me.
        Exemplo: '+55 (83) 99999-1234' -> '5583999991234'
        """
        if not self.telefone:
            return None
        return re.sub(r'\D', '', self.telefone)
    
    @property
    def idade(self):
        today = date.today()
        return today.year - self.data_nascimento.year - (
            (today.month, today.day) < (self.data_nascimento.month, self.data_nascimento.day)
        )
    
    @property
    def consentimento_ativo(self):
        """Retorna True se o último consentimento foi aceito"""
        ultimo = self.consentimentos.order_by('-data_registro').first()
        return ultimo.status == 'aceito' if ultimo else False
    

    @property
    def primeiro_nome(self):
        if not self.nome:
            return ""
        return self.nome.strip().split()[0]

    @property
    def ultimo_nome(self):
        if not self.nome or len(self.nome.strip().split()) == 1:
            return ""
        partes = self.nome.strip().split()
        return partes[-1] if len(partes) > 1 else partes[0]

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
    data_registro = models.DateTimeField(default=timezone.now)
    
    STATUS_CONSENTIMENTO = [
        ('aceito', 'Aceito'),
        ('revogado', 'Revogado'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CONSENTIMENTO)
    
    motivo_revogacao = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-data_registro']

    def __str__(self):
        return f"{self.gestante.nome} - {self.status} em {self.data_registro.strftime('%d/%m/%Y %H:%M')}"


class Avaliacao(models.Model):

    PARTO_CHOICES = [
        ('Vaginal', 'Vaginal'),
        ('Cesáreo', 'Cesáreo'),
    ]

    STATUS_LLM_CHOICES = [
        ('PENDING', 'Pendente'),
        ('PROCESSING', 'Processando LLM'),
        ('COMPLETED', 'LLM Concluído'),
        ('FAILED', 'LLM Falhou'),
    ]


    gestante = models.ForeignKey(Gestante, on_delete=models.CASCADE, related_name='questionarios')
    
    data_aplicacao = models.DateTimeField(verbose_name="Data da Avaliação", default=timezone.now)


    peso_atual = models.FloatField(
        verbose_name="Peso atual:" , null=True
    )

    idade_gestacional = models.PositiveIntegerField(verbose_name="Idade Gestacional (em semanas)", null=True)

    consultas_prenatal = models.PositiveIntegerField(verbose_name="Quantidade de consultas pré-natal", null=True)

    corrimento_vaginal = models.BooleanField(
        default=False, 
        verbose_name='Durante a gestação, você apresentou ou apresenta corrimento vaginal frequente?'
    )

    periodontite_carie = models.BooleanField(
        default=False, 
        verbose_name='Você já teve cárie e/ou periodontite (inflamação na gengiva) diagnosticada nesta gestação?'
    )

    hipertensao_gestacao = models.BooleanField(
        default=False, 
        verbose_name='Você foi diagnosticada com hipertensão (pressão alta) nesta gestação?'
    )

    diabetes_gestacao = models.BooleanField(
        default=False, 
        verbose_name='Você foi diagnosticada com diabetes nesta gestação?'
    )

    estresse_gestacao = models.BooleanField(
        default=False,
        verbose_name='Você passou por algum estresse durante a gestação (violência, sobrecarga de trabalho)?'
    )

    historico_familiar_alergia = models.BooleanField(
        default=False,
        verbose_name='Algum membro da sua família (pai, mãe, irmãos) tem histórico de asma, rinite ou dermatite?'
    )

    consumo_bebidas_adocadas = models.BooleanField(
        default=False,
        verbose_name='Na última semana você consumiu refrigerante e outras bebidas industrializadas adoçadas artificialmente, como suco de caixinha, achocolatados, etc?'
    )

    consumo_ultraprocessados = models.BooleanField(
        default=False,
        verbose_name='Na última semana você consumiu alimentos ultraprocessados (ex.: sorvete, salgadinhos, salsicha, linguiça, presuntos, macarrão instantâneo, biscoitos recheados, etc)?'
    )

    consumo_alcool = models.BooleanField(
        default=False,
        verbose_name='Você consome/consumiu bebidas alcoólicas (cerveja, vinho, vodka, cachaça, etc) nesta gestação?'
    )

    fumante_gestacao = models.BooleanField(
        default=False,
        verbose_name='Você tinha o hábito de fumar ou fumou nesta gestação?'
    )



    resultado_integralidade_saude = models.JSONField(null=True, blank=True)

    status_processamento_llm = models.CharField(
        max_length=20, 
        choices=STATUS_LLM_CHOICES, 
        default='PENDING' # Começa como pendente
    )

    status_processamento_pills = models.CharField(
        max_length=20, 
        choices=STATUS_LLM_CHOICES, 
        default='PENDING' # Começa como pendente
    )

    

    llm_sintese = models.TextField(
        null=True, 
        blank=True, 
        verbose_name="Síntese gerada pela LLM"
    )
    

    @property
    def ganho_peso(self):
        """Cálculo do ganho de peso durante a gestação"""
        if self.gestante and self.gestante.peso and self.peso_atual:
            return round(self.peso_atual - self.gestante.peso, 2)
        return None

    @property
    def top_fatores(self) -> list[str]:
        """
        Retorna a lista de top fatores do resultado de integralidade.
        Exemplo:
        ["maternalage_p", "family_h", "vagdischarge", "dailyssb_p", "blockupf2"]
        """
        if not self.resultado_integralidade_saude:
            return []

        return self.resultado_integralidade_saude.get("top_fatores", [])

    # --- Exemplo adicional: retornar em string, se quiser exibir direto no admin ---
    @property
    def top_fatores_str(self) -> str:
        """
        Retorna os top fatores como string separada por vírgula, útil para exibição.
        """
        return ", ".join(self.top_fatores)

    class Meta:
        verbose_name = 'Avaliacao'
        verbose_name_plural = 'Avaliações'
        ordering = ['gestante', 'data_aplicacao']  # Ordena por gestante e depois data

    def __str__(self):
        return f"Questionário de {self.gestante.nome} em {self.data_aplicacao.strftime('%d/%m/%Y')}"


locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

from django.db import models
from django.utils import timezone
from datetime import timedelta

class Pilula(models.Model):
    avaliacao = models.ForeignKey(
        'Avaliacao',
        on_delete=models.CASCADE,
        related_name='pilulas'
    )
    
    # Campos principais
    titulo = models.CharField(max_length=200, verbose_name="Título da Pílula")
    conteudo = models.TextField(verbose_name="Conteúdo da Pílula", blank=True, null=True)
    
    # Controle por semana
    semana_num = models.PositiveIntegerField(verbose_name="Número da semana", null=True, blank=True)

    # Datas e status
    data_geracao = models.DateTimeField(auto_now_add=True)
    data_envio = models.DateTimeField(null=True, blank=True, verbose_name="Data de envio")

    STATUS_CHOICES = [
        ('aguardando', 'Aguardando'),
        ('pendente', 'Pendente'),
        ('enviada', 'Enviada'),
        ('lida', 'Lida'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendente')

    class Meta:
        ordering = ['avaliacao', 'semana_num', 'data_geracao']
        verbose_name = "Pílula de Conhecimento"
        verbose_name_plural = "Pílulas de Conhecimento"

    # === Propriedades calculadas ===

    @property
    def data_inicio_envio(self):
        """Data a partir da qual a pílula pode ser enviada (base + 7 dias por semana)."""
        if not self.data_geracao or not self.semana_num:
            return None
        return self.data_geracao + timedelta(days=(self.semana_num - 1) * 7)

    @property
    def periodo_envio(self):
        """Retorna o intervalo (ex: '1 a 7 de outubro')."""
        inicio = self.data_inicio_envio
        if not inicio:
            return None
        fim = inicio + timedelta(days=6)
        # formata datas em estilo natural
        mes = inicio.strftime("%B").capitalize()
        return f"{inicio.day} a {fim.day} de {mes}"

    @property
    def semana_ord(self):
        """Retorna a forma ordinal (1ª, 2ª, 3ª...)"""
        if not self.semana_num:
            return None
        return f"{self.semana_num}ª"

    # === Métodos utilitários ===
    def marcar_enviada(self):
        """Atualiza o status e define a data de envio."""
        self.status = 'enviada'
        self.data_envio = timezone.now()
        self.save()

    def __str__(self):
        if self.semana_ord:
            return f"{self.semana_ord} semana - {self.titulo} ({self.status})"
        return f"{self.titulo} ({self.status})"
