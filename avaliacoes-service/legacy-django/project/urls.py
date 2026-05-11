from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('avaliacoes.urls')),
    path('fhir/', include('avaliacoes.fhir.urls')),
]