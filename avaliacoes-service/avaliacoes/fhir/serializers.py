"""
Serializers FHIR para o Avaliacoes Service.
Converte entre modelos Django e recursos FHIR.
"""
from fhir.resources.observation import Observation
from fhir.resources.questionnaire import Questionnaire
from fhir.resources.questionnaireresponse import QuestionnaireResponse
from fhir.resources.coding import Coding
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.reference import Reference
from rest_framework import serializers


class FHIRObservationSerializer(serializers.Serializer):
    """Serializer para converter entre Observation (Avaliação) e modelo Django."""
    
    fhir_id = serializers.CharField(read_only=True, source='id')
    status = serializers.ChoiceField(choices=['registered', 'preliminary', 'final', 'amended', 'corrected'])
    category = serializers.ListField(child=serializers.DictField(), required=False)
    code = serializers.DictField(required=False)
    subject = serializers.DictField(required=False)
    effective_date_time = serializers.DateTimeField(required=False)
    issued = serializers.DateTimeField(required=False)
    performer = serializers.ListField(child=serializers.DictField(), required=False)
    value = serializers.DictField(required=False)
    interpretation = serializers.ListField(child=serializers.DictField(), required=False)
    note = serializers.ListField(child=serializers.DictField(), required=False)
    component = serializers.ListField(child=serializers.DictField(), required=False)
    
    def to_fhir(self, instance):
        """Converte modelo Django Avaliacao para recurso FHIR Observation."""
        observation = Observation(
            id=str(instance.id),
            status='final',
            resource_type="Observation"
        )
        
        # Código da avaliação
        if hasattr(instance, 'tipo') and instance.tipo:
            coding = Coding(
                system="http://termino.hl7.org/CodeSystem/v3-ActCode",
                code=instance.tipo,
                display=str(instance)
            )
            codeable = CodeableConcept(coding=[coding])
            observation.code = codeable
        
        # Referência ao subject (gestante)
        if hasattr(instance, 'gestante') and instance.gestante:
            subject = Reference(
                reference=f"Patient/{instance.gestante.id}",
                display=str(instance.gestante)
            )
            observation.subject = subject
        
        # Data da avaliação
        if hasattr(instance, 'data_criacao') and instance.data_criacao:
            observation.effective_date_time = instance.data_criacao.isoformat()
            observation.issued = instance.data_criacao.isoformat()
        
        return observation
    
    def to_django(self, fhir_data):
        """Converte recurso FHIR Observation para dados Django."""
        # Extrair código
        code_value = None
        if fhir_data.get('code') and fhir_data['code'].get('coding'):
            code_value = fhir_data['code']['coding'][0].get('code')
        
        # Extrair subject ID
        subject_id = None
        if fhir_data.get('subject') and fhir_data['subject'].get('reference'):
            ref = fhir_data['subject']['reference']
            if ref.startswith('Patient/'):
                subject_id = ref.split('/')[1]
        
        return {
            'tipo': code_value,
            'gestante_id': subject_id,
        }


class FHIRQuestionnaireSerializer(serializers.Serializer):
    """Serializer para Questionnaire (Pílulas de Conhecimento)."""
    
    fhir_id = serializers.CharField(read_only=True, source='id')
    identifier = serializers.ListField(child=serializers.DictField(), required=False)
    version = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    title = serializers.CharField(required=False)
    status = serializers.ChoiceField(choices=['draft', 'active', 'retired', 'unknown'])
    date = serializers.DateTimeField(required=False)
    publisher = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    item = serializers.ListField(child=serializers.DictField(), required=False)
    
    def to_fhir(self, instance):
        """Converte modelo Pílula para recurso FHIR Questionnaire."""
        questionnaire = Questionnaire(
            id=str(instance.id),
            status='active',
            resource_type="Questionnaire"
        )
        
        if hasattr(instance, 'titulo'):
            questionnaire.title = instance.titulo
            questionnaire.name = instance.titulo
        
        if hasattr(instance, 'descricao'):
            questionnaire.description = instance.descricao
        
        return questionnaire
    
    def to_django(self, fhir_data):
        """Converte recurso FHIR Questionnaire para dados Django."""
        return {
            'titulo': fhir_data.get('title'),
            'descricao': fhir_data.get('description'),
        }


class FHIRQuestionnaireResponseSerializer(serializers.Serializer):
    """Serializer para QuestionnaireResponse (Respostas às Pílulas)."""
    
    fhir_id = serializers.CharField(read_only=True, source='id')
    questionnaire = serializers.DictField(required=False)
    status = serializers.ChoiceField(choices=['in-progress', 'completed', 'amended', 'entered-in-error'])
    subject = serializers.DictField(required=False)
    authored = serializers.DateTimeField(required=False)
    author = serializers.DictField(required=False)
    item = serializers.ListField(child=serializers.DictField(), required=False)
    
    def to_fhir(self, instance):
        """Converte modelo RespostaPílula para recurso FHIR QuestionnaireResponse."""
        qresponse = QuestionnaireResponse(
            id=str(instance.id),
            status='completed',
            resource_type="QuestionnaireResponse"
        )
        
        if hasattr(instance, 'data_resposta'):
            qresponse.authored = instance.data_resposta.isoformat()
        
        return questionnaire
    
    def to_django(self, fhir_data):
        """Converte recurso FHIR QuestionnaireResponse para dados Django."""
        return {}