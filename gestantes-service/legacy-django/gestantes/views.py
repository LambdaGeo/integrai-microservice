from rest_framework import viewsets, permissions
from .models import Gestante, ConsentimentoGestante
from .serializers import GestanteSerializer, ConsentimentoGestanteSerializer


class GestanteViewSet(viewsets.ModelViewSet):
    queryset = Gestante.objects.all()
    serializer_class = GestanteSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    search_fields = ['nome', 'telefone']
    filterset_fields = ['vulnerabilidade_social', 'usuario']


class ConsentimentoGestanteViewSet(viewsets.ModelViewSet):
    queryset = ConsentimentoGestante.objects.all()
    serializer_class = ConsentimentoGestanteSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['status', 'gestante']