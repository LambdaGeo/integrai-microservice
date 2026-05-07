from datetime import timedelta

from django.db import models
from django.utils import timezone


class Avaliacao(models.Model):

    STATUS_LLM_CHOICES = [
        ('PENDING', 'Pendente'),
        ('PROCESSING', 'Processando LLM'),
        ('COMPLETED', 'LLM Concluído'),
        ('FAILED', 'LLM Falhou'),
    ]

    gestante = models.ForeignKey('Gestante', on_delete=models.CASCADE, related_name='questionarios')
    data_aplicacao = models.DateTimeField(verbose_name="Data da Avaliação", default=timezone.now)
    peso_atual = models.FloatField(verbose_name="Peso atual:", null=True)
    idade_gestacional = models.PositiveIntegerField(verbose_name="Idade Gestacional (em semanas)", null=True)
    consultas_prenatal = models.PositiveIntegerField(verbose_name="Quantidade de consultas pré-natal", null=True)
    
    # Questionário SIM/P
    gestante = models.PositiveIntegerField(db_index=True)
    data_aplicacao = models.DateTimeField(verbose_name="Data da Avaliacao", default=timezone.now)
    peso_atual = models.FloatField(verbose_name="Peso atual:", null=True, blank=True)
    idade_gestacional = models.PositiveIntegerField(verbose_name="Idade Gestacional (em semanas)", null=True, blank=True)
    corrimento_vaginal = models.BooleanField(default=False, verbose_name='Corrimento vaginal frequente?')
    periodontite_carie = models.BooleanField(default=False, verbose_name='Cárie e/ou periodontite?')
    hipertensao_gestacao = models.BooleanField(default=False, verbose_name='Hipertensão na gestação?')
    diabetes_gestacao = models.BooleanField(default=False, verbose_name='Diabetes na gestação?')
    estresse_gestacao = models.BooleanField(default=False, verbose_name='Estresse durante gestação?')
    historico_familiar_alergia = models.BooleanField(default=False, verbose_name='Histórico familiar de alergia?')
    consumo_bebidas_adocadas = models.BooleanField(default=False, verbose_name='Consumo de bebidas adoçadas?')
    consumo_ultraprocessados = models.BooleanField(default=False, verbose_name='Consumo de ultraprocessados?')
    consumo_alcool = models.BooleanField(default=False, verbose_name='Consumo de álcool?')
    fumante_gestacao = models.BooleanField(default=False, verbose_name='Fumante?')

    resultado_integralidade_saude = models.JSONField(null=True, blank=True)
    status_processamento_llm = models.CharField(max_length=20, choices=STATUS_LLM_CHOICES, default='PENDING')
    status_processamento_pills = models.CharField(max_length=20, choices=STATUS_LLM_CHOICES, default='PENDING')
    llm_sintese = models.TextField(null=True, blank=True, verbose_name="Síntese gerada pela LLM")

    @property
    def ganho_peso(self):
        if self.gestante and self.gestante.peso and self.peso_atual:
            return round(self.peso_atual - self.gestante.peso, 2)
        return None

    @property
    def top_fatores(self):
        if not self.resultado_integralidade_saude:
            return []
        return self.resultado_integralidade_saude.get("top_fatores", [])

    @property
    def top_fatores_str(self):
        return ", ".join(self.top_fatores)

    class Meta:
        verbose_name = 'Avaliacao'
        verbose_name_plural = 'Avaliações'
        ordering = ['gestante', 'data_aplicacao']

    def __str__(self):
        return f"Questionário de {self.gestante.nome} em {self.data_aplicacao.strftime('%d/%m/%Y')}"


class Pilula(models.Model):
    avaliacao = models.ForeignKey(Avaliacao, on_delete=models.CASCADE, related_name='pilulas')
    titulo = models.CharField(max_length=200, verbose_name="Título da Pílula")
    conteudo = models.TextField(verbose_name="Conteúdo da Pílula", blank=True, null=True)
    semana_num = models.PositiveIntegerField(verbose_name="Número da semana", null=True, blank=True)
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

    @property
    def data_inicio_envio(self):
        if not self.data_geracao or not self.semana_num:
            return None
        return self.data_geracao + timedelta(days=(self.semana_num - 1) * 7)

    @property
    def periodo_envio(self):
        inicio = self.data_inicio_envio
        if not inicio:
            return None
        fim = inicio + timedelta(days=6)
        mes = inicio.strftime("%B").capitalize()
        return f"{inicio.day} a {fim.day} de {mes}"

    @property
    def semana_ord(self):
        if not self.semana_num:
            return None
        return f"{self.semana_num}ª"

    def marcar_enviada(self):
        self.status = 'enviada'
        self.data_envio = timezone.now()
        self.save()

    def __str__(self):
        if self.semana_ord:
            return f"{self.semana_ord} semana - {self.titulo} ({self.status})"
        return f"{self.titulo} ({self.status})"