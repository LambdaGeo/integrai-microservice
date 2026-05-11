from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from .models import Avaliacao, Pilula
from .serializers import AvaliacaoSerializer, PilulaSerializer
from .authorization import authorized_gestante_ids, can_access_gestante


class AvaliacaoViewSet(viewsets.ModelViewSet):
    queryset = Avaliacao.objects.none()
    serializer_class = AvaliacaoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['gestante', 'status_processamento_llm', 'status_processamento_pills']

    def get_queryset(self):
        return Avaliacao.objects.filter(gestante__in=authorized_gestante_ids(self.request.auth))

    def perform_create(self, serializer):
        gestante_id = serializer.validated_data.get('gestante')
        if not can_access_gestante(gestante_id, self.request.auth):
            raise PermissionDenied("Access denied")
        serializer.save()


class PilulaViewSet(viewsets.ModelViewSet):
    queryset = Pilula.objects.none()
    serializer_class = PilulaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['avaliacao', 'status']

    def get_queryset(self):
        return Pilula.objects.filter(avaliacao__gestante__in=authorized_gestante_ids(self.request.auth))

    def perform_create(self, serializer):
        avaliacao = serializer.validated_data.get('avaliacao')
        if avaliacao and not can_access_gestante(avaliacao.gestante, self.request.auth):
            raise PermissionDenied("Access denied")
        serializer.save()


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health(request):
    return Response({"status": "healthy"})
