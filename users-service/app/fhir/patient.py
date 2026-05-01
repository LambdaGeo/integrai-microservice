"""
FHIR Patient Resource - Map Usuario to FHIR Patient
"""
from typing import Optional, List
from datetime import datetime

from fhir.resources.patient import Patient
from fhir.resources.humanname import HumanName
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.identifier import Identifier
from fhir.resources.resource import Resource

from app.models.usuario import Usuario


def usuario_to_fhir_patient(usuario: Usuario) -> Patient:
    """
    Convert Usuario model to FHIR Patient resource
    """
    # Identifier - CPF como identifier
    identifiers = [
        Identifier(
            use="official",
            type={
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                    "code": "CP",
                    "display": "Patient's Medicare Number"
                }]
            },
            value=usuario.username
        )
    ]
    
    # Name - Como não temos nome no Usuario, usamos username
    names = [
        HumanName(
            use="official",
            text=usuario.username  # Usando CPF como nome temporário
        )
    ]
    
    # Contact - Email
    telecoms = []
    if usuario.email:
        telecoms.append(
            ContactPoint(
                system="email",
                value=usuario.email,
                use="home"
            )
        )
    
    # Build Patient resource
    patient = Patient(
        resourceType="Patient",
        id=str(usuario.id),
        identifier=identifiers,
        name=names,
        telecom=telecoms if telecoms else None,
        active=usuario.is_active,
        gender="unknown"  # Default - não temos essa info
    )
    
    return patient


def fhir_patient_to_usuario(patient: Patient, password: str) -> dict:
    """
    Convert FHIR Patient resource to Usuario create dict
    """
    # Extract CPF from identifier
    cpf = None
    if patient.identifier:
        for identifier in patient.identifier:
            if identifier.value:
                cpf = identifier.value
                break
    
    # Extract email from telecom
    email = None
    if patient.telecom:
        for telecom in patient.telecom:
            if telecom.system == "email":
                email = telecom.value
                break
    
    return {
        "username": cpf or "",
        "email": email,
        "password": password
    }