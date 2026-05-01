"""
URLs FHIR para o Avaliacoes Service.
Rotas no padrão FHIR: /fhir/Observation, /fhir/Questionnaire, etc.
"""
from django.urls import path
from . import views

app_name = 'fhir'

urlpatterns = [
    # FHIR endpoints
    path('Observation', views.ObservationView.as_view(), name='observation-list'),
    path('Observation/<int:pk>', views.ObservationDetailView.as_view(), name='observation-detail'),
    path('Questionnaire', views.QuestionnaireView.as_view(), name='questionnaire-list'),
    path('QuestionnaireResponse', views.QuestionnaireResponseView.as_view(), name='questionnaireresponse-list'),
    path('metadata', views.MetadataView.as_view(), name='capability-statement'),
    path('', views.FHIRRootView.as_view(), name='fhir-root'),
]