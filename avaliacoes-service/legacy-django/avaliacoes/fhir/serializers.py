"""
Serializers FHIR para o Avaliacoes Service.
Converte entre modelos Django e recursos FHIR.
"""
import json

from fhir.resources.questionnaire import Questionnaire
from fhir.resources.questionnaireresponse import QuestionnaireResponse
from rest_framework import serializers


FHIR_SYSTEM = "https://integrai.ufma.br/fhir/CodeSystem/avaliacao-gestacional"
OBSERVATION_CODE = "avaliacao-gestacional"
EXT_RESULTADO = "https://integrai.ufma.br/fhir/StructureDefinition/avaliacao-resultado-integralidade-saude"
EXT_STATUS_LLM = "https://integrai.ufma.br/fhir/StructureDefinition/avaliacao-status-processamento-llm"
EXT_STATUS_PILLS = "https://integrai.ufma.br/fhir/StructureDefinition/avaliacao-status-processamento-pills"
EXT_LLM_SINTESE = "https://integrai.ufma.br/fhir/StructureDefinition/avaliacao-llm-sintese"

COMPONENTS = {
    "peso_atual": {
        "display": "Peso atual",
        "value": "valueQuantity",
        "unit": "kg",
        "code": "kg",
    },
    "idade_gestacional": {
        "display": "Idade gestacional em semanas",
        "value": "valueInteger",
    },
    "consultas_prenatal": {
        "display": "Quantidade de consultas pre-natal",
        "value": "valueInteger",
    },
    "corrimento_vaginal": {
        "display": "Corrimento vaginal frequente",
        "value": "valueBoolean",
    },
    "periodontite_carie": {
        "display": "Carie e/ou periodontite",
        "value": "valueBoolean",
    },
    "hipertensao_gestacao": {
        "display": "Hipertensao na gestacao",
        "value": "valueBoolean",
    },
    "diabetes_gestacao": {
        "display": "Diabetes na gestacao",
        "value": "valueBoolean",
    },
    "estresse_gestacao": {
        "display": "Estresse durante gestacao",
        "value": "valueBoolean",
    },
    "historico_familiar_alergia": {
        "display": "Historico familiar de alergia",
        "value": "valueBoolean",
    },
    "consumo_bebidas_adocadas": {
        "display": "Consumo de bebidas adocadas",
        "value": "valueBoolean",
    },
    "consumo_ultraprocessados": {
        "display": "Consumo de ultraprocessados",
        "value": "valueBoolean",
    },
    "consumo_alcool": {
        "display": "Consumo de alcool",
        "value": "valueBoolean",
    },
    "fumante_gestacao": {
        "display": "Fumante na gestacao",
        "value": "valueBoolean",
    },
}


class FHIRObservationSerializer(serializers.Serializer):
    """Serializer para converter entre Observation (Avaliacao) e modelo Django."""

    fhir_id = serializers.CharField(read_only=True, source="id")
    resourceType = serializers.CharField(required=False)
    status = serializers.ChoiceField(
        choices=["registered", "preliminary", "final", "amended", "corrected"],
        required=False,
    )
    category = serializers.ListField(child=serializers.DictField(), required=False)
    code = serializers.DictField(required=False)
    subject = serializers.DictField(required=False)
    effectiveDateTime = serializers.DateTimeField(required=False)
    issued = serializers.DateTimeField(required=False)
    performer = serializers.ListField(child=serializers.DictField(), required=False)
    value = serializers.DictField(required=False)
    interpretation = serializers.ListField(child=serializers.DictField(), required=False)
    note = serializers.ListField(child=serializers.DictField(), required=False)
    component = serializers.ListField(child=serializers.DictField(), required=False)
    extension = serializers.ListField(child=serializers.DictField(), required=False)

    def to_fhir(self, instance):
        """Converte modelo Django Avaliacao para recurso FHIR Observation."""
        observation = {
            "resourceType": "Observation",
            "id": str(instance.id),
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "survey",
                    "display": "Survey",
                }]
            }],
            "code": {
                "coding": [{
                    "system": FHIR_SYSTEM,
                    "code": OBSERVATION_CODE,
                    "display": "Avaliacao gestacional",
                }],
                "text": "Avaliacao gestacional",
            },
            "subject": {"reference": f"Patient/{instance.gestante}"},
            "component": [],
            "extension": [
                {"url": EXT_STATUS_LLM, "valueString": instance.status_processamento_llm},
                {"url": EXT_STATUS_PILLS, "valueString": instance.status_processamento_pills},
            ],
        }

        if instance.data_aplicacao:
            observation["effectiveDateTime"] = instance.data_aplicacao.isoformat()
            observation["issued"] = instance.data_aplicacao.isoformat()

        if instance.resultado_integralidade_saude is not None:
            observation["extension"].append({
                "url": EXT_RESULTADO,
                "valueString": json.dumps(instance.resultado_integralidade_saude),
            })

        if instance.llm_sintese:
            observation["extension"].append({
                "url": EXT_LLM_SINTESE,
                "valueString": instance.llm_sintese,
            })

        for field, config in COMPONENTS.items():
            value = getattr(instance, field, None)
            if value is None:
                continue

            component = {
                "code": {
                    "coding": [{
                        "system": FHIR_SYSTEM,
                        "code": field,
                        "display": config["display"],
                    }],
                    "text": config["display"],
                }
            }

            if config["value"] == "valueQuantity":
                component["valueQuantity"] = {
                    "value": value,
                    "unit": config["unit"],
                    "system": "http://unitsofmeasure.org",
                    "code": config["code"],
                }
            else:
                component[config["value"]] = value

            observation["component"].append(component)

        return observation

    def to_django(self, fhir_data):
        """Converte recurso FHIR Observation para dados Django."""
        data = {}

        subject_id = None
        if fhir_data.get("subject") and fhir_data["subject"].get("reference"):
            ref = fhir_data["subject"]["reference"]
            if ref.startswith("Patient/"):
                subject_id = ref.split("/")[1]
        if subject_id:
            data["gestante"] = subject_id

        if fhir_data.get("effectiveDateTime"):
            data["data_aplicacao"] = fhir_data["effectiveDateTime"]

        for component in fhir_data.get("component", []) or []:
            field = self._component_code(component)
            if field not in COMPONENTS:
                continue
            data[field] = self._component_value(component)

        for extension in fhir_data.get("extension", []) or []:
            url = extension.get("url")
            if url == EXT_STATUS_LLM:
                data["status_processamento_llm"] = extension.get("valueString")
            elif url == EXT_STATUS_PILLS:
                data["status_processamento_pills"] = extension.get("valueString")
            elif url == EXT_LLM_SINTESE:
                data["llm_sintese"] = extension.get("valueString")
            elif url == EXT_RESULTADO and extension.get("valueString"):
                data["resultado_integralidade_saude"] = json.loads(extension["valueString"])

        return data

    def _component_code(self, component):
        for coding in component.get("code", {}).get("coding", []) or []:
            if coding.get("system") == FHIR_SYSTEM:
                return coding.get("code")
        return None

    def _component_value(self, component):
        if "valueBoolean" in component:
            return component["valueBoolean"]
        if "valueInteger" in component:
            return component["valueInteger"]
        if "valueQuantity" in component:
            return component["valueQuantity"].get("value")
        if "valueString" in component:
            return component["valueString"]
        return None


class FHIRQuestionnaireSerializer(serializers.Serializer):
    """Serializer para Questionnaire (Pilulas de Conhecimento)."""

    fhir_id = serializers.CharField(read_only=True, source="id")
    identifier = serializers.ListField(child=serializers.DictField(), required=False)
    version = serializers.CharField(required=False)
    name = serializers.CharField(required=False)
    title = serializers.CharField(required=False)
    status = serializers.ChoiceField(choices=["draft", "active", "retired", "unknown"])
    date = serializers.DateTimeField(required=False)
    publisher = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    item = serializers.ListField(child=serializers.DictField(), required=False)

    def to_fhir(self, instance):
        """Converte modelo Pilula para recurso FHIR Questionnaire."""
        questionnaire = Questionnaire(
            id=str(instance.id),
            status="active",
            resource_type="Questionnaire",
        )

        if hasattr(instance, "titulo"):
            questionnaire.title = instance.titulo
            questionnaire.name = instance.titulo

        if hasattr(instance, "descricao"):
            questionnaire.description = instance.descricao

        return questionnaire

    def to_django(self, fhir_data):
        """Converte recurso FHIR Questionnaire para dados Django."""
        return {
            "titulo": fhir_data.get("title"),
            "descricao": fhir_data.get("description"),
        }


class FHIRQuestionnaireResponseSerializer(serializers.Serializer):
    """Serializer para QuestionnaireResponse (Respostas as Pilulas)."""

    fhir_id = serializers.CharField(read_only=True, source="id")
    questionnaire = serializers.DictField(required=False)
    status = serializers.ChoiceField(choices=["in-progress", "completed", "amended", "entered-in-error"])
    subject = serializers.DictField(required=False)
    authored = serializers.DateTimeField(required=False)
    author = serializers.DictField(required=False)
    item = serializers.ListField(child=serializers.DictField(), required=False)

    def to_fhir(self, instance):
        """Converte modelo RespostaPilula para recurso FHIR QuestionnaireResponse."""
        qresponse = QuestionnaireResponse(
            id=str(instance.id),
            status="completed",
            resource_type="QuestionnaireResponse",
        )

        if hasattr(instance, "data_resposta"):
            qresponse.authored = instance.data_resposta.isoformat()

        return qresponse

    def to_django(self, fhir_data):
        """Converte recurso FHIR QuestionnaireResponse para dados Django."""
        return {}
