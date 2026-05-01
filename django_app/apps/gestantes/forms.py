from django import forms

import django_rq

from apps.gestantes.models import Gestante, Avaliacao

import re

from . import services # usar sincrono por enquanto, depois configurar redis/celery

# --- INÍCIO DA INTEGRAÇÃO COM A API R ---
from apps.gestantes.tasks import gerar_sintese_llm_task, gerar_pilulas_task

class GestanteForms(forms.ModelForm):
    class Meta:
        model = Gestante
        exclude = ["usuario"]
        
        # Definindo a ordem explícita
        fields = [
            'nome',
            'foto',
            'telefone',
            'data_nascimento',
            'altura',
            'peso',
            'vulnerabilidade_social'
            
        ]

        labels = {
            'data_cadastro': 'Data da inserção',
            'usuario': 'Usuário',
        }

        help_texts = {
            'vulnerabilidade_social': (
                '<span class="fw-bold text-danger">⚠ NÃO PERGUNTAR À GESTANTE!</span><br>'
                'Este campo deve ser marcado por você com base nas suas visitas domiciliares: '
            ),
        }

        widgets = {
            'nome': forms.TextInput(attrs={'class':'form-control'}),
            'foto': forms.FileInput(attrs={'class':'form-control'}),
            'data_fotografia': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type':'date', 'class':'form-control'}
            ),
            
            'telefone': forms.TextInput(attrs={
            'class': 'form-control',
                'placeholder': 'Ex.: (83) 99999-1234 — preferencialmente WhatsApp'
            }),

            'altura': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'inputmode': 'decimal', 'placeholder': 'Digite a altura (ex: 1,58)'}
            ),
            'data_nascimento': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'type': 'date', 'class': 'form-control'}
            ),


        }
    
    def clean_altura(self):
        altura = self.cleaned_data.get('altura')
        if altura is None:
            raise forms.ValidationError("Informe a altura da gestante.")
        if isinstance(altura, str):
            altura = altura.replace(',', '.')
        try:
            return float(altura)
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
    
class AvaliacaoForm(forms.ModelForm):
    class Meta:
        model = Avaliacao
        exclude = [
            'gestante',
            'resultado_integralidade_saude',
            'llm_sintese',
            'data_aplicacao',
            'status_processamento_llm',
            'status_processamento_pills',
            'peso_atual','idade_gestacional', 'consultas_prenatal'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove valores iniciais dos campos de marcar
        for field_name, field in self.fields.items():
            if isinstance(field, forms.BooleanField) or isinstance(field.widget, forms.RadioSelect):
                field.initial = None

    
    def save(self, commit: bool = True, gestante: Gestante | None = None) -> Avaliacao:
            # 1. Cria a instância (sem salvar no DB)
            instance = super().save(commit=False)

            if gestante is None and not instance.gestante_id:
                raise ValueError("A avaliação deve estar associada a uma gestante.")

            if gestante is not None:
                instance.gestante = gestante

            if commit:
                # 1️⃣ Salva a avaliação
                instance.save()

                # 2️⃣ Processa o risco de forma síncrona
                services.processar_risco_avaliacao(instance.id)

                # 3️⃣ Atualiza o objeto
                instance.refresh_from_db()

                # 4️⃣ Dispara a geração da síntese LLM em background
                django_rq.enqueue(gerar_sintese_llm_task, instance.id)

                
                django_rq.enqueue(gerar_pilulas_task, instance.id)

            return instance