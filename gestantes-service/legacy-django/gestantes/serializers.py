from rest_framework import serializers
from .models import Gestante, ConsentimentoGestante


class GestanteSerializer(serializers.ModelSerializer):
    agente_nome = serializers.CharField(source='usuario.username', read_only=True)
    imc = serializers.ReadOnlyField()
    idade = serializers.ReadOnlyField()
    imc_classificacao = serializers.ReadOnlyField()
    
    class Meta:
        model = Gestante
        fields = [
            'id', 'nome', 'data_nascimento', 'peso', 'altura', 'telefone',
            'vulnerabilidade_social', 'foto', 'data_cadastro', 'usuario',
            'agente_nome', 'imc', 'idade', 'imc_classificacao', 'telefone_whatsapp'
        ]
        read_only_fields = ['id', 'data_cadastro', 'imc', 'idade']


class ConsentimentoGestanteSerializer(serializers.ModelSerializer):
    gestante_nome = serializers.CharField(source='gestante.nome', read_only=True)
    
    class Meta:
        model = ConsentimentoGestante
        fields = ['id', 'gestante', 'gestante_nome', 'usuario', 'data_registro', 'status', 'motivo_revogacao']