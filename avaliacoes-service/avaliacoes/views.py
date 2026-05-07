from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Avaliacao, Pilula
from .serializers import AvaliacaoSerializer, PilulaSerializer


class AvaliacaoViewSet(viewsets.ModelViewSet):
    queryset = Avaliacao.objects.all()
    serializer_class = AvaliacaoSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['gestante', 'status_processamento_llm', 'status_processamento_pills']


class PilulaViewSet(viewsets.ModelViewSet):
    queryset = Pilula.objects.all()
    serializer_class = PilulaSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['avaliacao', 'status']


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health(request):
    return Response({"status": "healthy"})
