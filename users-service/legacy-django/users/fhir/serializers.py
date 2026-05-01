"""
Serializers FHIR para o Users Service.
Converte entre modelos Django e recursos FHIR.
"""
from fhir.resources.practitioner import Practitioner
from fhir.resources.practitionerrole import PractitionerRole
from fhir.resources.humanname import HumanName
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.address import Address
from rest_framework import serializers


class FHIRPractitionerSerializer(serializers.Serializer):
    """Serializer para converter entre Practitioner e modelo Django."""
    
    fhir_id = serializers.CharField(read_only=True, source='id')
    identifier = serializers.ListField(child=serializers.DictField(), required=False)
    active = serializers.BooleanField(default=True)
    name = serializers.ListField(child=serializers.DictField(), required=False)
    telecom = serializers.ListField(child=serializers.DictField(), required=False)
    address = serializers.ListField(child=serializers.DictField(), required=False)
    gender = serializers.ChoiceField(choices=['male', 'female', 'other', 'unknown'])
    birth_date = serializers.DateField(required=False)
    
    def to_fhir(self, instance):
        """Converte modelo Django para recurso FHIR Practitioner."""
        practitioner = Practitioner(
            id=str(instance.id),
            active=instance.is_active,
            resource_type="Practitioner"
        )
        
        # Nome
        if instance.first_name or instance.last_name:
            name = HumanName(
                family=instance.last_name,
                given=[instance.first_name] if instance.first_name else []
            )
            practitioner.name = [name]
        
        # Contato
        if instance.email:
            telecom = [
                ContactPoint(
                    system="email",
                    value=instance.email,
                    use="work"
                )
            ]
            practitioner.telecom = telecom
        
        return practitioner
    
    def to_django(self, fhir_data):
        """Converte recurso FHIR Practitioner para dados Django."""
        return {
            'email': self._get_telecom_value(fhir_data.get('telecom', []), 'email'),
            'first_name': self._get_first_name(fhir_data.get('name', [])),
            'last_name': self._get_last_name(fhir_data.get('name', [])),
            'is_active': fhir_data.get('active', True),
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


class FHIRPractitionerRoleSerializer(serializers.Serializer):
    """Serializer para converter entre PractitionerRole e modelo Django."""
    
    fhir_id = serializers.CharField(read_only=True, source='id')
    active = serializers.BooleanField(default=True)
    practitioner = serializers.DictField(required=False)
    role = serializers.ListField(child=serializers.DictField(), required=False)
    specialty = serializers.ListField(child=serializers.DictField(), required=False)
    location = serializers.ListField(child=serializers.DictField(), required=False)
    organization = serializers.DictField(required=False)
    telecom = serializers.ListField(child=serializers.DictField(), required=False)