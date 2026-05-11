"""
Views FHIR para o Avaliacoes Service.
Endpoints que expõem a API no padrão FHIR.
"""
import logging

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from avaliacoes.authorization import authorized_gestante_ids, can_access_gestante
from .serializers import FHIRObservationSerializer, FHIRQuestionnaireSerializer, FHIRQuestionnaireResponseSerializer
from avaliacoes.models import Avaliacao
from avaliacoes.services import calcular_e_salvar_risco


logger = logging.getLogger(__name__)


class ObservationView(APIView):
    """Endpoint FHIR para Observation (Avaliações)."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Lista todas as Observations (GET /Observation)."""
        fhir_id = request.query_params.get('_id')

        if fhir_id:
            try:
                avaliacao = Avaliacao.objects.get(id=fhir_id)
                serializer = FHIRObservationSerializer()
                fhir_resource = serializer.to_fhir(avaliacao)
                return Response(fhir_resource, status=status.HTTP_200_OK)
            except Avaliacao.DoesNotExist:
                return Response({
                    'resourceType': 'OperationOutcome',
                    'issue': [{'severity': 'error', 'code': 'not-found'}]
                }, status=status.HTTP_404_NOT_FOUND)

        avaliacoes = Avaliacao.objects.filter(gestante__in=authorized_gestante_ids(request.auth))
        subject = request.query_params.get('subject') or request.query_params.get('patient')
        if subject:
            gestante_id = subject.removeprefix('Patient/')
            if not can_access_gestante(gestante_id, request.auth):
                avaliacoes = Avaliacao.objects.none()
            else:
                avaliacoes = avaliacoes.filter(gestante=gestante_id)

        count = request.query_params.get('_count')
        if count and count.isdigit():
            avaliacoes = avaliacoes[:int(count)]

        entries = []

        for avaliacao in avaliacoes:
            serializer = FHIRObservationSerializer()
            fhir_resource = serializer.to_fhir(avaliacao)
            entries.append({
                'resource': fhir_resource,
                'fullUrl': f"Observation/{avaliacao.id}"
            })

        bundle = {
            'resourceType': 'Bundle',
            'type': 'searchset',
            'total': len(entries),
            'entry': entries
        }

        return Response(bundle, status=status.HTTP_200_OK)
    
    def post(self, request):
        """Cria uma nova Observation (POST /Observation)."""
        serializer = FHIRObservationSerializer(data=request.data)
        
        if serializer.is_valid():
            data = serializer.to_django(request.data)
            if not can_access_gestante(data.get('gestante'), request.auth):
                return Response({
                    'resourceType': 'OperationOutcome',
                    'issue': [{'severity': 'error', 'code': 'forbidden', 'diagnostics': 'Access denied'}]
                }, status=status.HTTP_403_FORBIDDEN)
            avaliacao = Avaliacao.objects.create(**data)
            try:
                calcular_e_salvar_risco(avaliacao, access_token=request.auth)
            except Exception:
                logger.exception("Erro ao calcular risco da avaliacao %s", avaliacao.id)

            fhir_resource = serializer.to_fhir(avaliacao)
            return Response(fhir_resource, status=status.HTTP_201_CREATED)

        return Response({
            'resourceType': 'OperationOutcome',
            'issue': [{'severity': 'error', 'code': 'invalid', 'diagnostics': str(serializer.errors)}]
        }, status=status.HTTP_400_BAD_REQUEST)


class ObservationDetailView(APIView):
    """Endpoint FHIR para Observation específica."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """GET /Observation/{id}"""
        try:
            avaliacao = Avaliacao.objects.get(id=pk)
            if not can_access_gestante(avaliacao.gestante, request.auth):
                return Response({
                    'resourceType': 'OperationOutcome',
                    'issue': [{'severity': 'error', 'code': 'not-found'}]
                }, status=status.HTTP_404_NOT_FOUND)
            serializer = FHIRObservationSerializer()
            fhir_resource = serializer.to_fhir(avaliacao)
            return Response(fhir_resource, status=status.HTTP_200_OK)
        except Avaliacao.DoesNotExist:
            return Response({
                'resourceType': 'OperationOutcome',
                'issue': [{'severity': 'error', 'code': 'not-found'}]
            }, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, pk):
        """PUT /Observation/{id}"""
        try:
            avaliacao = Avaliacao.objects.get(id=pk)
            if not can_access_gestante(avaliacao.gestante, request.auth):
                return Response({
                    'resourceType': 'OperationOutcome',
                    'issue': [{'severity': 'error', 'code': 'not-found'}]
                }, status=status.HTTP_404_NOT_FOUND)
            serializer = FHIRObservationSerializer(data=request.data)
            
            if serializer.is_valid():
                data = serializer.to_django(request.data)
                if data.get('gestante') and not can_access_gestante(data.get('gestante'), request.auth):
                    return Response({
                        'resourceType': 'OperationOutcome',
                        'issue': [{'severity': 'error', 'code': 'forbidden', 'diagnostics': 'Access denied'}]
                    }, status=status.HTTP_403_FORBIDDEN)
                for key, value in data.items():
                    if hasattr(avaliacao, key):
                        setattr(avaliacao, key, value)
                avaliacao.save()

                fhir_resource = serializer.to_fhir(avaliacao)
                return Response(fhir_resource, status=status.HTTP_200_OK)

            return Response({
                'resourceType': 'OperationOutcome',
                'issue': [{'severity': 'error', 'code': 'invalid', 'diagnostics': str(serializer.errors)}]
            }, status=status.HTTP_400_BAD_REQUEST)

        except Avaliacao.DoesNotExist:
            return Response({
                'resourceType': 'OperationOutcome',
                'issue': [{'severity': 'error', 'code': 'not-found'}]
            }, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, pk):
        """DELETE /Observation/{id}"""
        try:
            avaliacao = Avaliacao.objects.get(id=pk)
            if not can_access_gestante(avaliacao.gestante, request.auth):
                return Response({
                    'resourceType': 'OperationOutcome',
                    'issue': [{'severity': 'error', 'code': 'not-found'}]
                }, status=status.HTTP_404_NOT_FOUND)
            avaliacao.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Avaliacao.DoesNotExist:
            return Response({
                'resourceType': 'OperationOutcome',
                'issue': [{'severity': 'error', 'code': 'not-found'}]
            }, status=status.HTTP_404_NOT_FOUND)


class QuestionnaireView(APIView):
    """Endpoint FHIR para Questionnaire (Pílulas de Conhecimento)."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Lista todos os Questionnaires."""
        return Response({
            'resourceType': 'Bundle',
            'type': 'searchset',
            'total': 0,
            'entry': []
        }, status=status.HTTP_200_OK)


class QuestionnaireResponseView(APIView):
    """Endpoint FHIR para QuestionnaireResponse (Respostas às Pílulas)."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Lista todos os QuestionnaireResponses."""
        return Response({
            'resourceType': 'Bundle',
            'type': 'searchset',
            'total': 0,
            'entry': []
        }, status=status.HTTP_200_OK)


class MetadataView(APIView):
    """Capability Statement (metadata)."""
    
    permission_classes = [IsAuthenticated]
    
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
                    'type': 'Observation',
                    'interaction': [
                        {'code': 'read'},
                        {'code': 'search-type'},
                        {'code': 'create'},
                        {'code': 'update'},
                        {'code': 'delete'}
                    ]
                }, {
                    'type': 'Questionnaire',
                    'interaction': [
                        {'code': 'read'},
                        {'code': 'search-type'}
                    ]
                }, {
                    'type': 'QuestionnaireResponse',
                    'interaction': [
                        {'code': 'read'},
                        {'code': 'search-type'},
                        {'code': 'create'}
                    ]
                }]
            }]
        }
        return Response(capability, status=status.HTTP_200_OK)


class FHIRRootView(APIView):
    """Raiz da API FHIR."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """GET / - Servidor FHIR."""
        return Response({
            'resourceType': 'CapabilityStatement',
            'status': 'active',
            'fhirVersion': '4.0.1',
            'format': ['json']
        }, status=status.HTTP_200_OK)
