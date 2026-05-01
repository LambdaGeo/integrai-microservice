from rest_framework import serializers
from .models import Usuario, AgenteProfile


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'is_active', 'is_staff', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class AgenteProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AgenteProfile
        fields = ['id', 'username', 'nome', 'foto', 'area', 'ubs', 'primeiro_nome']