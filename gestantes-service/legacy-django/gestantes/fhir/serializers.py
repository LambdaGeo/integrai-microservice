"""
Serializers FHIR para o Gestantes Service.
Converte entre modelos Django e recursos FHIR.
"""
from fhir.resources.patient import Patient
from fhir.resources.humanname import HumanName
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.address import Address
from fhir.resources.identifier import Identifier
from fhir.resources.extension import Extension
from rest_framework import serializers


class FHIRPatientSerializer(serializers.Serializer):
    """Serializer para converter entre Patient (Gestante) e modelo Django."""
    
    fhir_id = serializers.CharField(read_only=True, source='id')
    identifier = serializers.ListField(child=serializers.DictField(), required=False)
    active = serializers.BooleanField(default=True)
    name = serializers.ListField(child=serializers.DictField(), required=False)
    telecom = serializers.ListField(child=serializers.DictField(), required=False)
    gender = serializers.ChoiceField(choices=['male', 'female', 'other', 'unknown'])
    birth_date = serializers.DateField(required=False)
    address = serializers.ListField(child=serializers.DictField(), required=False)
    
    def to_fhir(self, instance):
        """Converte modelo Django Gestante para recurso FHIR Patient."""
        patient = Patient(
            id=str(instance.id),
            active=True,
            resource_type="Patient"
        )
        
        # Nome
        if instance.nome:
            name = HumanName(
                family=instance.sobrenome if hasattr(instance, 'sobrenome') else None,
                given=[instance.nome] if instance.nome else []
            )
            patient.name = [name]
        
        # Contato
        if hasattr(instance, 'telefone') and instance.telefone:
            telecom = [
                ContactPoint(
                    system="phone",
                    value=instance.telefone,
                    use="mobile"
                )
            ]
            patient.telecom = telecom
        
        # Gênero - gestante é sempre female
        patient.gender = "female"
        
        # Data de nascimento
        if hasattr(instance, 'data_nascimento') and instance.data_nascimento:
            patient.birth_date = instance.data_nascimento.isoformat()
        
        return patient
    
    def to_django(self, fhir_data):
        """Converte recurso FHIR Patient para dados Django."""
        return {
            'nome': self._get_first_name(fhir_data.get('name', [])),
            'sobrenome': self._get_last_name(fhir_data.get('name', [])),
            'telefone': self._get_telecom_value(fhir_data.get('telecom', []), 'phone'),
            'data_nascimento': fhir_data.get('birth_date'),
        }
    
    def _get_telecom_value(self, telecom_list, system):
        for telecom in telecom_list:
            if telecom.get('system') == system:
                return telecom.get('value')
        return None
    
    def _get_first_name(self, name_list):
        for name in name_list:
            given = name.get('given', [])
            if given:
                return given[0]
        return None
    
    def _get_last_name(self, name_list):
        for name in name_list:
            if name.get('family'):
                return name.get('family')
        return None


class FHIRPregnancyObservationSerializer(serializers.Serializer):
    """Serializer para dados de gravidez (Observation)."""
    
    fhir_id = serializers.CharField(read_only=True, source='id')
    status = serializers.ChoiceField(choices=['registered', 'preliminary', 'final', 'amended'])
    category = serializers.ListField(child=serializers.DictField(), required=False)
    code = serializers.DictField(required=False)
    subject = serializers.DictField(required=False)
    effective_date_time = serializers.DateTimeField(required=False)
    value = serializers.DictField(required=False)
    note = serializers.ListField(child=serializers.DictField(), required=False)