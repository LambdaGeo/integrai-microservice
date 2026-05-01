"""
Views FHIR para o Users Service.
Endpoints que expõem a API no padrão FHIR.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .serializers import FHIRPractitionerSerializer, FHIRPractitionerRoleSerializer
from users.models import Usuario


class PractitionerView(APIView):
    """Endpoint FHIR para Practitioner (Usuários/Agentes)."""
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Lista todos os Practitioners (GET /Practitioner)."""
        fhir_id = request.query_params.get('_id')
        
        if fhir_id:
            try:
                usuario = Usuario.objects.get(id=fhir_id)
                serializer = FHIRPractitionerSerializer()
                fhir_resource = serializer.to_fhir(usuario)
                return Response(fhir_resource.dict(), status=status.HTTP_200_OK)
            except Usuario.DoesNotExist:
                return Response({
                    'resourceType': 'OperationOutcome',
                    'issue': [{'severity': 'error', 'code': 'not-found'}]
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Lista todos
        usuarios = Usuario.objects.all()
        entries = []
        
        for usuario in usuarios:
            serializer = FHIRPractitionerSerializer()
            fhir_resource = serializer.to_fhir(usuario)
            entries.append({
                'resource': fhir_resource.dict(),
                'fullUrl': f"Practitioner/{usuario.id}"
            })
        
        bundle = {
            'resourceType': 'Bundle',
            'type': 'searchset',
            'total': len(entries),
            'entry': entries
        }
        
        return Response(bundle, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Cria um novo Practitioner (POST /Practitioner)."""
        serializer = FHIRPractitionerSerializer(data=request.data)
        
        if serializer.is_valid():
            data = serializer.to_django(request.data)
            usuario = Usuario.objects.create(**data)
            
            # Retorna o recurso criado
            fhir_resource = serializer.to_fhir(usuario)
            return Response(fhir_resource.dict(), status=status.HTTP_201_CREATED)
        
        return Response({
            'resourceType': 'OperationOutcome',
            'issue': [{'severity': 'error', 'code': 'invalid', 'diagnostics': str(serializer.errors)}]
        }, status=status.HTTP_400_BAD_REQUEST)


class PractitionerDetailView(APIView):
    """Endpoint FHIR para Practitioner específico."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        """GET /Practitioner/{id}"""
        try:
            usuario = Usuario.objects.get(id=pk)
            serializer = FHIRPractitionerSerializer()
            fhir_resource = serializer.to_fhir(usuario)
            return Response(fhir_resource.dict(), status=status.HTTP_200_OK)
        except Usuario.DoesNotExist:
            return Response({
                'resourceType': 'OperationOutcome',
                'issue': [{'severity': 'error', 'code': 'not-found'}]
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, pk):
        """PUT /Practitioner/{id}"""
        try:
            usuario = Usuario.objects.get(id=pk)
            serializer = FHIRPractitionerSerializer(data=request.data)
            
            if serializer.is_valid():
                data = serializer.to_django(request.data)
                for key, value in data.items():
                    setattr(usuario, key, value)
                usuario.save()
                
                fhir_resource = serializer.to_fhir(usuario)
                return Response(fhir_resource.dict(), status=status.HTTP_200_OK)
            
            return Response({
                'resourceType': 'OperationOutcome',
                'issue': [{'severity': 'error', 'code': 'invalid', 'diagnostics': str(serializer.errors)}]
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Usuario.DoesNotExist:
            return Response({
                'resourceType': 'OperationOutcome',
                'issue': [{'severity': 'error', 'code': 'not-found'}]
            }, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, pk):
        """DELETE /Practitioner/{id}"""
        try:
            usuario = Usuario.objects.get(id=pk)
            usuario.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Usuario.DoesNotExist:
            return Response({
                'resourceType': 'OperationOutcome',
                'issue': [{'severity': 'error', 'code': 'not-found'}]
            }, status=status.HTTP_404_NOT_FOUND)


class PractitionerRoleView(APIView):
    """Endpoint FHIR para PractitionerRole (Perfis de Agente)."""
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Lista todos os PractitionerRoles."""
        # Implementação similar para AgenteProfile
        return Response({
            'resourceType': 'Bundle',
            'type': 'searchset',
            'total': 0,
            'entry': []
        }, status=status.HTTP_200_OK)


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
                    'type': 'Practitioner',
                    'interaction': [
                        {'code': 'read'},
                        {'code': 'search-type'},
                        {'code': 'create'},
                        {'code': 'update'},
                        {'code': 'delete'}
                    ]
                }, {
                    'type': 'PractitionerRole',
                    'interaction': [
                        {'code': 'read'},
                        {'code': 'search-type'}
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