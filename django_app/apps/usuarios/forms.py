
from django import forms
from django.contrib import auth
from django.contrib.auth.password_validation import validate_password
import re


def validar_cpf(cpf):
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) != 11: return False
    if cpf == cpf[0] * 11: return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    if resto == 10: resto = 0
    if resto != int(cpf[9]): return False
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    if resto == 10: resto = 0
    if resto != int(cpf[10]): return False
    return True


class LoginForms(forms.Form):
    nome_login = forms.CharField(
        label='CPF',
        required=True,
        max_length=14,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'XXX.XXX.XXX-XX',
        })
    )
    senha = forms.CharField(
        label='Senha',
        required=True,
        max_length=70,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua senha',
        }),
    )

    user_cache = None

    def clean(self):
        cleaned_data = super().clean()
        nome_login = cleaned_data.get('nome_login')
        senha = cleaned_data.get('senha')

        if nome_login:
            nome_login = ''.join(filter(str.isdigit, nome_login))
            cleaned_data['nome_login'] = nome_login

        self.user_cache = auth.authenticate(
            username=nome_login,
            password=senha
        )

        if self.user_cache is None:
            raise forms.ValidationError(
                'CPF ou senha inválidos.',
                code='invalid_login'
            )
        return cleaned_data

    def get_user(self):
        return self.user_cache


class CadastroForms(forms.Form):
    nome_cadastro = forms.CharField(
        label='CPF',
        required=True,
        max_length=14,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'XXX.XXX.XXX-XX'
        })
    )
    nome_completo = forms.CharField(
        label='Nome Completo',
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex.: João da Silva'
        })
    )
    senha_1 = forms.CharField(
        label='Senha',
        required=True,
        max_length=70,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua senha'
        })
    )
    senha_2 = forms.CharField(
        label='Confirme sua senha',
        required=True,
        max_length=70,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite sua senha novamente'
        })
    )
    email = forms.EmailField(
        label='Email',
        required=True,
        max_length=100,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex.: joaosilva@xpto.com'
        })
    )
    area = forms.CharField(
        label='Área de atuação',
        required=True,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex.: Bairro Central'
        })
    )
    ubs = forms.CharField(
        label='Unidade Básica de Saúde (UBS)',
        required=True,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'UBS Turu'
        })
    )
    foto = forms.ImageField(
        label="Foto",
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    def clean_nome_cadastro(self):
        cpf_original = self.cleaned_data.get('nome_cadastro')
        if not validar_cpf(cpf_original):
            raise forms.ValidationError('CPF inválido.')
        return re.sub(r'[^0-9]', '', cpf_original)

    # REMOVIDO: validação de unicidade — agora é responsabilidade do users-service

    def clean_senha_1(self):
        senha_1 = self.cleaned_data.get("senha_1")
        if senha_1:
            validate_password(senha_1)
        return senha_1

    def clean_senha_2(self):
        senha_1 = self.cleaned_data.get('senha_1')
        senha_2 = self.cleaned_data.get('senha_2')
        if senha_1 and senha_2 and senha_1 != senha_2:
            raise forms.ValidationError('As senhas não são iguais.')
        return senha_2


class PerfilUpdateUserForm(forms.Form):
    """Form simples — sem ModelForm, sem dependência de banco local."""
    email = forms.EmailField(
        label="Email",
        max_length=100,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )


class PerfilUpdateProfileForm(forms.Form):
    """Form simples — sem ModelForm, sem dependência de AgenteProfile."""
    nome = forms.CharField(
        label="Nome Completo",
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    area = forms.CharField(
        label="Área de atuação",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    ubs = forms.CharField(
        label="Unidade Básica de Saúde (UBS)",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    foto = forms.ImageField(
        label="Foto",
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

# from django import forms
# #from django.contrib.auth.models import User
# from django.contrib import auth
# from .models import AgenteProfile # Importe seus modelos

# from django.contrib.auth.password_validation import validate_password

# import re

# from django.contrib.auth import get_user_model
# User = get_user_model()

# def validar_cpf(cpf):
#     cpf = re.sub(r'[^0-9]', '', cpf)
#     if len(cpf) != 11: return False
#     if cpf == cpf[0] * 11: return False
#     soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
#     resto = (soma * 10) % 11
#     if resto == 10: resto = 0
#     if resto != int(cpf[9]): return False
#     soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
#     resto = (soma * 10) % 11
#     if resto == 10: resto = 0
#     if resto != int(cpf[10]): return False
#     return True


# class LoginForms(forms.Form):
#     # 1. SUAS DEFINIÇÕES DE CAMPO ORIGINAIS (SEM '...')
#     nome_login=forms.CharField(
#         label='CPF',
#         required=True,
#         max_length=14,
#         widget=forms.TextInput(
#             attrs={
#                 'class': 'form-control',
#                 'placeholder': 'XXX.XXX.XXX-XX',
#             }
#         )
#     )
#     senha=forms.CharField(
#         label='Senha', 
#         required=True, 
#         max_length=70,
#         widget=forms.PasswordInput(
#             attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Digite sua senha',
#             }
#         ),
#     )

#     # Variável para guardar o usuário autenticado
#     user_cache = None

#     # 2. OS NOVOS MÉTODOS (para validar o login aqui)
#     def clean(self):
#         cleaned_data = super().clean()
#         nome_login = cleaned_data.get('nome_login')
#         senha = cleaned_data.get('senha')

#         if nome_login:
#             # limpar . e -
#             nome_login = ''.join(filter(str.isdigit, nome_login))
#             cleaned_data['nome_login'] = nome_login

#         self.user_cache = auth.authenticate(
#             username=nome_login,
#             password=senha
#         )

#         if self.user_cache is None:
#             raise forms.ValidationError(
#                 'CPF ou senha inválidos.',
#                 code='invalid_login'
#             )
#         return cleaned_data

#     def get_user(self):
#         # Um método helper para a view pegar o usuário
#         return self.user_cache



# class CadastroForms(forms.Form):

#     nome_cadastro = forms.CharField(
#         label='CPF',
#         required=True,
#         max_length=14,
#         widget=forms.TextInput(attrs={
#             'class': 'form-control',
#             'placeholder': 'XXX.XXX.XXX-XX'
#         })
#     )

#     nome_completo = forms.CharField(
#         label='Nome Completo',
#         required=True,
#         max_length=150,
#         widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: João da Silva'})
#     )

#     senha_1 = forms.CharField(
#         label='Senha',
#         required=True,
#         max_length=70,
#         widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Digite sua senha'})
#     )
#     senha_2 = forms.CharField(
#         label='Confirme sua senha',
#         required=True,
#         max_length=70,
#         widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Digite sua senha novamente'})
#     )

#     email = forms.EmailField(
#         label='Email',
#         required=True,
#         max_length=100,
#         widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: joaosilva@xpto.com'})
#     )

#     # --------------------
#     # Seus campos de Perfil (estão perfeitos)
#     # --------------------


#     area = forms.CharField(
#         label='Área de atuação',
#         required=True,
#         max_length=100,
#         widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: Bairro Central'})
#     )

#     ubs = forms.CharField(
#         label='Unidade Básica de Saúde (UBS)',
#         required=True,
#         max_length=100,
#         widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'UBS Turu'})
#     )
#     foto = forms.ImageField(
#         label="Foto",
#         required=False,
#         widget=forms.FileInput(attrs={'class': 'form-control'})
#     )

#     # --------------------
#     # Validações (Refatoradas)
#     # --------------------

#     def clean_nome_cadastro(self):
#         cpf_original = self.cleaned_data.get('nome_cadastro')

#         # valida formato
#         if not validar_cpf(cpf_original):
#             raise forms.ValidationError('CPF inválido.')

#         cpf_numerico = re.sub(r'[^0-9]', '', cpf_original)

#         # verifica unicidade no usuário
#         if User.objects.filter(username=cpf_numerico).exists():
#             raise forms.ValidationError("Este CPF já está em uso.")

#         return cpf_numerico

#     def clean_email(self):
#         email = self.cleaned_data.get('email')
        
#         # MELHORIA 2: Validação de unicidade do email
#         if User.objects.filter(email=email).exists():
#             raise forms.ValidationError('Este email já está em uso.')
            
#         return email
#     '''
#     def clean_cpf(self):
#         cpf_original = self.cleaned_data.get('cpf')
        
#         if not validar_cpf(cpf_original):
#             raise forms.ValidationError('CPF inválido.')
        
#         # MELHORIA 3: Limpa o CPF para salvar apenas números
#         cpf_numerico = re.sub(r'[^0-9]', '', cpf_original)

#         # MELHORIA 4: Validação de unicidade do CPF
#         if AgenteProfile.objects.filter(cpf=cpf_numerico).exists():
#             raise forms.ValidationError('Este CPF já pertence a outro agente.')

#         return cpf_numerico # Retorna o CPF limpo (apenas números)
#     '''

#     def clean_senha_1(self):
#         senha_1 = self.cleaned_data.get("senha_1")
#         if senha_1:
#             validate_password(senha_1)  # ← valida com as regras do Django
#         return senha_1

#     def clean_senha_2(self):
#         senha_1 = self.cleaned_data.get('senha_1')
#         senha_2 = self.cleaned_data.get('senha_2')

#         if senha_1 and senha_2 and senha_1 != senha_2:
#             raise forms.ValidationError('As senhas não são iguais.')
#         return senha_2
    



# class PerfilUpdateUserForm(forms.ModelForm):

#     email = forms.EmailField(
#         label="Email",
#         max_length=100,
#         widget=forms.EmailInput(attrs={'class': 'form-control'})
#     )

#     class Meta:
#         model = User
#         fields = ["email"]

#     # --- Valida unicidade somente se realmente mudaram ---
#     def clean_username(self):
#         cpf_raw = self.cleaned_data.get("username")

#         if not validar_cpf(cpf_raw):
#             raise forms.ValidationError("CPF inválido.")

#         cpf = ''.join(filter(str.isdigit, cpf_raw))

#         qs = User.objects.filter(username=cpf).exclude(pk=self.instance.pk)
#         if qs.exists():
#             raise forms.ValidationError("Este CPF já está em uso.")
#         return cpf

#     def clean_email(self):
#         email = self.cleaned_data.get("email")
#         qs = User.objects.filter(email=email).exclude(pk=self.instance.pk)
#         if qs.exists():
#             raise forms.ValidationError("Este email já está em uso.")
#         return email



# class PerfilUpdateProfileForm(forms.ModelForm):
#     nome = forms.CharField(
#         label="Nome Completo",
#         max_length=150,
#         widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex.: João da Silva'})
#     )

#     area = forms.CharField(
#         label="Área de atuação",
#         max_length=100,
#         widget=forms.TextInput(attrs={'class': 'form-control'})
#     )

#     UBS = forms.CharField(
#         label="Unidade Básica de Saúde (UBS)",
#         max_length=100,
#         widget=forms.TextInput(attrs={'class': 'form-control'})
#     )

#     foto = forms.ImageField(
#         label="Foto",
#         required=False,
#         widget=forms.FileInput(attrs={'class': 'form-control'})
#     )

#     class Meta:
#         model = AgenteProfile
#         fields = ["nome", "area", "UBS", "foto"]
