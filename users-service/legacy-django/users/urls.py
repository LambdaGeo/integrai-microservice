from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UsuarioViewSet, AgenteProfileViewSet

router = DefaultRouter()
router.register(r'usuarios', UsuarioViewSet)
router.register(r'agentes', AgenteProfileViewSet)

urlpatterns = [
    path('', include(router.urls)),
]