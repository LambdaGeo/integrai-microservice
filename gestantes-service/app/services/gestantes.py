"""
Business rules for Gestantes domain.
"""
from datetime import date


def calcular_idade(data_nascimento: date) -> int:
    hoje = date.today()
    return hoje.year - data_nascimento.year - (
        (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day)
    )


def validar_regras_gestante(data_nascimento: date, peso: int, altura: float) -> None:
    idade = calcular_idade(data_nascimento)
    if idade < 10 or idade > 60:
        raise ValueError("A idade deve estar entre 10 e 60 anos.")
    if peso < 30 or peso > 200:
        raise ValueError("O peso deve estar entre 30 e 200 kg.")
    if altura < 1.0 or altura > 2.5:
        raise ValueError("A altura deve estar entre 1.0 e 2.5 metros.")

