from rest_framework import viewsets, permissions
from .models import Avaliacao, Pilula
from .serializers import AvaliacaoSerializer, PilulaSerializer


class AvaliacaoViewSet(viewsets.ModelViewSet):
    queryset = Avaliacao.objects.all()
    serializer_class = AvaliacaoSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['gestante', 'status_processamento_llm', 'status_processamento_pills']


class PilulaViewSet(viewsets.ModelViewSet):
    queryset = Pilula.objects.all()
    serializer_class = PilulaSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['avaliacao', 'status']