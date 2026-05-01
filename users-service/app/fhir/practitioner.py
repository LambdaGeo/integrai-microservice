"""
FHIR Practitioner Resource - Map AgenteProfile to FHIR Practitioner
"""
from typing import Optional

from fhir.resources.practitioner import Practitioner
from fhir.resources.humanname import HumanName
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.identifier import Identifier
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding

from app.models.usuario import AgenteProfile


def agenteprofile_to_fhir_practitioner(profile: AgenteProfile) -> Practitioner:
    """
    Convert AgenteProfile model to FHIR Practitioner resource
    """
    # Name
    names = [
        HumanName(
            use="official",
            text=profile.nome,
            family=profile.nome.split()[-1] if profile.nome else None,
            given=[profile.primeiro_nome] if profile.primeiro_nome else None
        )
    ]
    
    # Contact - Area e UBS como telecom
    telecoms = []
    if profile.area:
        telecoms.append(
            ContactPoint(
                system="other",
                value=profile.area,
                use="work",
                rank=1
            )
        )
    if profile.ubs:
        telecoms.append(
            ContactPoint(
                system="other",
                value=profile.ubs,
                use="work",
                rank=2
            )
        )
    
    # Build Practitioner resource
    practitioner = Practitioner(
        resourceType="Practitioner",
        id=str(profile.id),
        identifier=[
            Identifier(
                use="official",
                value=str(profile.user_id)
            )
        ],
        name=names,
        telecom=telecoms if telecoms else None,
        active=True
    )
    
    return practitioner


def fhir_practitioner_to_agenteprofile(practitioner: Practitioner) -> dict:
    """
    Convert FHIR Practitioner resource to AgenteProfile create dict
    """
    nome = None
    if practitioner.name:
        for name in practitioner.name:
            if name.text:
                nome = name.text
                break
            if name.family:
                nome = name.family
                break
    
    area = None
    ubs = None
    if practitioner.telecom:
        for telecom in practitioner.telecom:
            if telecom.system == "other":
                if telecom.rank == 1:
                    area = telecom.value
                elif telecom.rank == 2:
                    ubs = telecom.value
    
    user_id = None
    if practitioner.identifier:
        for identifier in practitioner.identifier:
            if identifier.value:
                user_id = int(identifier.value)
                break
    
    return {
        "user_id": user_id,
        "nome": nome,
        "area": area,
        "ubs": ubs
    }