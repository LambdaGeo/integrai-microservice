from django import forms

import django_rq
import re
from datetime import datetime

# DESABILITADO: Modelos migrados para microservice gestantes-service
# from apps.gestantes.models import Gestante, Avaliacao
# from . import services
# from apps.gestantes.tasks import gerar_sintese_llm_task, gerar_pilulas_task


# Forma simples para criação de gestantes via API microservice
# Esta classe não herda de ModelForm pois o modelo foi migrado
class GestanteForms(forms.Form):
    """Formulário para criar/editar gestantes via API microservice"""
    
    nome = forms.CharField(
        max_length=100,
        required=True,
        label="Nome Completo",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da gestante'})
    )
    
    foto = forms.ImageField(
        required=False,
        label="Foto",
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    telefone = forms.CharField(
        max_length=20,
        required=False,
        label="Telefone (preferencialmente WhatsApp)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex.: (83) 99999-1234'
        })
    )
    
    data_nascimento = forms.DateField(
        required=True,
        label="Data de Nascimento",
        widget=forms.DateInput(
            format='%Y-%m-%d',
            attrs={'type': 'date', 'class': 'form-control'}
        )
    )
    
    altura = forms.FloatField(
        required=True,
        label="Altura (m)",
        widget=forms.NumberInput(
            attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Ex: 1.58'}
        )
    )
    
    peso = forms.IntegerField(
        required=True,
        label="Peso pré-gestacional (kg)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 70'})
    )
    
    VULNERABILIDADE_CHOICES = [
        (True, 'Sim'),
        (False, 'Não'),
    ]
    vulnerabilidade_social = forms.TypedChoiceField(
        required=False,
        choices=VULNERABILIDADE_CHOICES,
        coerce=lambda value: value == 'True',
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Com base nas suas visitas domiciliares, considera essa gestante em vulnerabilidade social?'
    )
    
    def clean_altura(self):
        altura = self.cleaned_data.get('altura')
        if altura is None:
            raise forms.ValidationError("Informe a altura da gestante.")
        if isinstance(altura, str):
            altura = altura.replace(',', '.')
        try:
            valor = float(altura)
            if valor < 1.0 or valor > 2.5:
                raise forms.ValidationError("A altura deve estar entre 1.0 e 2.5 metros.")
            return valor
        except ValueError:
            raise forms.ValidationError("Informe um número válido para a altura (ex: 1,65)")
        
    def clean_telefone(self):
        telefone = self.cleaned_data.get("telefone")

        if not telefone:
            return telefone  # opcional

        numeros = re.sub(r'\D', '', telefone)

        # já veio com +55
        if numeros.startswith("55") and len(numeros) in [12, 13]:
            return f"+{numeros}"

        # veio sem +55 → valida BR
        if len(numeros) not in [10, 11]:
            raise forms.ValidationError("Informe um telefone válido com DDD (10 ou 11 dígitos).")

        return f"+55{numeros}"
    
    def clean_peso(self):
        peso = self.cleaned_data.get('peso')
        if peso and (peso < 30 or peso > 200):
            raise forms.ValidationError("O peso deve estar entre 30 e 200 kg.")
        return peso


# DESABILITADO: Classes que usam modelos migrados para microservice
# 
# class AvaliacaoForm(forms.ModelForm):
#     class Meta:
#         model = Avaliacao
#         exclude = [
#             'gestante',
#             'resultado_integralidade_saude',
#             'llm_sintese',
#             'data_aplicacao',
#             'status_processamento_llm',
#             'status_processamento_pills',
#             'peso_atual','idade_gestacional', 'consultas_prenatal'
#         ]
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         for field_name, field in self.fields.items():
#             if isinstance(field, forms.BooleanField) or isinstance(field.widget, forms.RadioSelect):
#                 field.initial = None
#
#     def save(self, commit: bool = True, gestante: Gestante | None = None) -> Avaliacao:
#         instance = super().save(commit=False)
#         if gestante is not None:
#             instance.gestante = gestante
#         if commit:
#             instance.save()
#             services.processar_risco_avaliacao(instance.id)
#             instance.refresh_from_db()
#             django_rq.enqueue(gerar_sintese_llm_task, instance.id)
#             django_rq.enqueue(gerar_pilulas_task, instance.id)
#         return instance