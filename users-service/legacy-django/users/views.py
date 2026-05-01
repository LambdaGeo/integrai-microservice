from rest_framework import viewsets, permissions
from .models import Usuario, AgenteProfile
from .serializers import UsuarioSerializer, AgenteProfileSerializer


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    search_fields = ['username', 'email']
    filterset_fields = ['is_active', 'is_staff']


class AgenteProfileViewSet(viewsets.ModelViewSet):
    queryset = AgenteProfile.objects.all()
    serializer_class = AgenteProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]