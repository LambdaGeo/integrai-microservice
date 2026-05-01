"""
URLs FHIR para o Users Service.
Rotas no padrão FHIR: /fhir/Practitioner, /fhir/PractitionerRole, etc.
"""
from django.urls import path
from . import views

app_name = 'fhir'

urlpatterns = [
    # FHIR endpoints
    path('Practitioner', views.PractitionerView.as_view(), name='practitioner-list'),
    path('Practitioner/<int:pk>', views.PractitionerDetailView.as_view(), name='practitioner-detail'),
    path('PractitionerRole', views.PractitionerRoleView.as_view(), name='practitionerrole-list'),
    path('PractitionerRole/<int:pk>', views.PractitionerRoleView.as_view(), name='practitionerrole-detail'),
    path('metadata', views.MetadataView.as_view(), name='capability-statement'),
    path('', views.FHIRRootView.as_view(), name='fhir-root'),
]