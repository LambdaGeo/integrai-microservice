"""
Views FHIR para o Gestantes Service.
Endpoints que expõem a API no padrão FHIR.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .serializers import FHIRPatientSerializer
from gestantes.models import Gestante


class PatientView(APIView):
    """Endpoint FHIR para Patient (Gestantes)."""
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Lista todos os Patients (GET /Patient)."""
        fhir_id = request.query_params.get('_id')
        
        if fhir_id:
            try:
                gestante = Gestante.objects.get(id=fhir_id)
                serializer = FHIRPatientSerializer()
                fhir_resource = serializer.to_fhir(gestante)
                return Response(fhir_resource.dict(), status=status.HTTP_200_OK)
            except Gestante.DoesNotExist:
                return Response({
                    'resourceType': 'OperationOutcome',
                    'issue': [{'severity': 'error', 'code': 'not-found'}]
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Lista todos
        gestantes = Gestante.objects.all()
        entries = []
        
        for gestante in gestantes:
            serializer = FHIRPatientSerializer()
            fhir_resource = serializer.to_fhir(gestante)
            entries.append({
                'resource': fhir_resource.dict(),
                'fullUrl': f"Patient/{gestante.id}"
            })
        
        bundle = {
            'resourceType': 'Bundle',
            'type': 'searchset',
            'total': len(entries),
            'entry': entries
        }
        
        return Response(bundle, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Cria um novo Patient (POST /Patient)."""
        serializer = FHIRPatientSerializer(data=request.data)
        
        if serializer.is_valid():
            data = serializer.to_django(request.data)
            gestante = Gestante.objects.create(**data)
            
            fhir_resource = serializer.to_fhir(gestante)
            return Response(fhir_resource.dict(), status=status.HTTP_201_CREATED)
        
        return Response({
            'resourceType': 'OperationOutcome',
            'issue': [{'severity': 'error', 'code': 'invalid', 'diagnostics': str(serializer.errors)}]
        }, status=status.HTTP_400_BAD_REQUEST)


class PatientDetailView(APIView):
    """Endpoint FHIR para Patient específico."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        """GET /Patient/{id}"""
        try:
            gestante = Gestante.objects.get(id=pk)
            serializer = FHIRPatientSerializer()
            fhir_resource = serializer.to_fhir(gestante)
            return Response(fhir_resource.dict(), status=status.HTTP_200_OK)
        except Gestante.DoesNotExist:
            return Response({
                'resourceType': 'OperationOutcome',
                'issue': [{'severity': 'error', 'code': 'not-found'}]
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, pk):
        """PUT /Patient/{id}"""
        try:
            gestante = Gestante.objects.get(id=pk)
            serializer = FHIRPatientSerializer(data=request.data)
            
            if serializer.is_valid():
                data = serializer.to_django(request.data)
                for key, value in data.items():
                    if hasattr(gestante, key):
                        setattr(gestante, key, value)
                gestante.save()
                
                fhir_resource = serializer.to_fhir(gestante)
                return Response(fhir_resource.dict(), status=status.HTTP_200_OK)
            
            return Response({
                'resourceType': 'OperationOutcome',
                'issue': [{'severity': 'error', 'code': 'invalid', 'diagnostics': str(serializer.errors)}]
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Gestante.DoesNotExist:
            return Response({
                'resourceType': 'OperationOutcome',
                'issue': [{'severity': 'error', 'code': 'not-found'}]
            }, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, pk):
        """DELETE /Patient/{id}"""
        try:
            gestante = Gestante.objects.get(id=pk)
            gestante.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Gestante.DoesNotExist:
            return Response({
                'resourceType': 'OperationOutcome',
                'issue': [{'severity': 'error', 'code': 'not-found'}]
            }, status=status.HTTP_404_NOT_FOUND)


class MetadataView(APIView):
    """Capability Statement (metadata)."""
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        """GET /metadata - Capability Statement."""
        capability = {
            'resourceType': 'CapabilityStatement',
            'status': 'active',
            'date': '2026-04-26',
            'kind': 'instance',
            'fhirVersion': '4.0.1',
            'format': ['json'],
            'rest': [{
                'mode': 'server',
                'resource': [{
                    'type': 'Patient',
                    'interaction': [
                        {'code': 'read'},
                        {'code': 'search-type'},
                        {'code': 'create'},
                        {'code': 'update'},
                        {'code': 'delete'}
                    ]
                }]
            }]
        }
        return Response(capability, status=status.HTTP_200_OK)


class FHIRRootView(APIView):
    """Raiz da API FHIR."""
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        """GET / - Servidor FHIR."""
        return Response({
            'resourceType': 'CapabilityStatement',
            'status': 'active',
            'fhirVersion': '4.0.1',
            'format': ['json']
        }, status=status.HTTP_200_OK)