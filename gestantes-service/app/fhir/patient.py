"""
FHIR Patient mapping for Gestante.
"""
from datetime import date
import re
from typing import Any

from fhir.resources.patient import Patient
from pydantic import ValidationError

from app.models.gestante import Gestante

GESTANTE_PATIENT_PROFILE = "https://integrai.ufma.br/fhir/StructureDefinition/GestantePatient"
EXT_PESO = "https://integrai.ufma.br/fhir/StructureDefinition/gestante-peso-pre"
EXT_ALTURA = "https://integrai.ufma.br/fhir/StructureDefinition/gestante-altura"
EXT_VULNERABILIDADE = "https://integrai.ufma.br/fhir/StructureDefinition/gestante-vulnerabilidade-social"
EXT_USUARIO_ID = "https://integrai.ufma.br/fhir/StructureDefinition/gestante-usuario-id"


def _split_name(full_name: str) -> tuple[str, list[str]]:
    parts = full_name.split()
    if not parts:
        return "", []
    if len(parts) == 1:
        return parts[0], [parts[0]]
    return parts[-1], parts[:-1]


def gestante_to_fhir_patient(gestante: Gestante) -> dict[str, Any]:
    family, given = _split_name(gestante.nome or "")
    payload: dict[str, Any] = {
        "resourceType": "Patient",
        "id": str(gestante.id),
        "meta": {"profile": [GESTANTE_PATIENT_PROFILE]},
        "active": True,
        "gender": "female",
        "name": [
            {
                "use": "official",
                "text": gestante.nome,
                "family": family or None,
                "given": given or None,
            }
        ],
        "birthDate": gestante.data_nascimento.isoformat(),
        "identifier": [
            {
                "use": "official",
                "system": "https://integrai.ufma.br/fhir/NamingSystem/gestante-id",
                "value": str(gestante.id),
            }
        ],
        "extension": [
            {"url": EXT_PESO, "valueInteger": gestante.peso},
            {"url": EXT_ALTURA, "valueDecimal": gestante.altura},
            {"url": EXT_VULNERABILIDADE, "valueBoolean": gestante.vulnerabilidade_social},
        ],
    }
    if gestante.usuario_id is not None:
        payload["extension"].append({"url": EXT_USUARIO_ID, "valueInteger": gestante.usuario_id})
    if gestante.telefone:
        payload["telecom"] = [
            {"system": "phone", "value": gestante.telefone, "use": "mobile"},
        ]

    return Patient.model_validate(payload).model_dump(mode="json", by_alias=True, exclude_none=True)


def fhir_patient_to_gestante(body: dict[str, Any], *, require_domain_fields: bool) -> dict[str, Any]:
    try:
        patient = Patient.model_validate(body)
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc

    nome = None
    if patient.name:
        first_name = patient.name[0]
        if first_name.text:
            nome = first_name.text
        else:
            given = " ".join(first_name.given or [])
            family = first_name.family or ""
            nome = f"{given} {family}".strip() or None

    phone = None
    if patient.telecom:
        for item in patient.telecom:
            if item.system == "phone":
                phone = item.value
                break

    birth_date = getattr(patient, "birthDate", None)
    if birth_date is None:
        raise ValueError("FHIR Patient precisa de birthDate para criar/atualizar gestante.")

    birth_value = birth_date if isinstance(birth_date, date) else date.fromisoformat(str(birth_date))

    extensions = getattr(patient, "extension", []) or []
    peso = _extract_extension_value(extensions, EXT_PESO, "valueInteger")
    altura = _extract_extension_value(extensions, EXT_ALTURA, "valueDecimal")
    vulnerabilidade = _extract_extension_value(extensions, EXT_VULNERABILIDADE, "valueBoolean")
    usuario_id = _extract_extension_value(extensions, EXT_USUARIO_ID, "valueInteger")

    if require_domain_fields:
        missing = []
        if peso is None:
            missing.append("extension:peso")
        if altura is None:
            missing.append("extension:altura")
        if vulnerabilidade is None:
            missing.append("extension:vulnerabilidade_social")
        if missing:
            raise ValueError(
                "FHIR Patient incompleto para dominio gestante. Campos obrigatorios ausentes: "
                + ", ".join(missing)
            )

    return {
        "nome": nome or "Sem Nome",
        "data_nascimento": birth_value,
        "telefone": phone,
        "peso": int(peso) if peso is not None else None,
        "altura": float(altura) if altura is not None else None,
        "vulnerabilidade_social": bool(vulnerabilidade) if vulnerabilidade is not None else None,
        "usuario_id": int(usuario_id) if usuario_id is not None else None,
    }


def match_identifier(gestante: Gestante, identifier: str) -> bool:
    if str(gestante.id) == identifier:
        return True
    phone = gestante.telefone or ""
    return bool(phone and re.sub(r"\D", "", phone) == re.sub(r"\D", "", identifier))


def _extract_extension_value(extensions, url: str, attr: str):
    for ext in extensions:
        if getattr(ext, "url", None) == url:
            return getattr(ext, attr, None)
    return None
