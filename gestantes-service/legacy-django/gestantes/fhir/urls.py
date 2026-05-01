"""
URLs FHIR para o Gestantes Service.
Rotas no padrão FHIR: /fhir/Patient, /fhir/Observation, etc.
"""
from django.urls import path
from . import views

app_name = 'fhir'

urlpatterns = [
    # FHIR endpoints
    path('Patient', views.PatientView.as_view(), name='patient-list'),
    path('Patient/<int:pk>', views.PatientDetailView.as_view(), name='patient-detail'),
    path('metadata', views.MetadataView.as_view(), name='capability-statement'),
    path('', views.FHIRRootView.as_view(), name='fhir-root'),
]