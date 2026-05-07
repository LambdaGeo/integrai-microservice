from rest_framework import serializers
from .models import Avaliacao, Pilula


class AvaliacaoSerializer(serializers.ModelSerializer):
    gestante_nome = serializers.SerializerMethodField()
    ganho_peso = serializers.ReadOnlyField()
    top_fatores_str = serializers.ReadOnlyField()
    
    class Meta:
        model = Avaliacao
        fields = [
            'id', 'gestante', 'gestante_nome', 'data_aplicacao', 'peso_atual',
            'idade_gestacional', 'consultas_prenatal', 'corrimento_vaginal',
            'periodontite_carie', 'hipertensao_gestacao', 'diabetes_gestacao',
            'estresse_gestacao', 'historico_familiar_alergia', 'consumo_bebidas_adocadas',
            'consumo_ultraprocessados', 'consumo_alcool', 'fumante_gestacao',
            'resultado_integralidade_saude', 'status_processamento_llm',
            'status_processamento_pills', 'llm_sintese', 'ganho_peso', 'top_fatores_str'
        ]
        read_only_fields = ['id', 'data_aplicacao']

    def get_gestante_nome(self, obj):
        return f"Gestante {obj.gestante}"


class PilulaSerializer(serializers.ModelSerializer):
    avaliacao_gestante = serializers.SerializerMethodField()
    semana_ord = serializers.ReadOnlyField()
    periodo_envio = serializers.ReadOnlyField()
    
    class Meta:
        model = Pilula
        fields = [
            'id', 'avaliacao', 'avaliacao_gestante', 'titulo', 'conteudo',
            'semana_num', 'semana_ord', 'data_geracao', 'data_envio',
            'status', 'periodo_envio'
        ]
        read_only_fields = ['id', 'data_geracao']

    def get_avaliacao_gestante(self, obj):
        return f"Gestante {obj.avaliacao.gestante}"
