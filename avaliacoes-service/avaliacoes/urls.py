from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AvaliacaoViewSet, PilulaViewSet, health

router = DefaultRouter()
router.register(r'avaliacoes', AvaliacaoViewSet)
router.register(r'pilulas', PilulaViewSet)

urlpatterns = [
    path('health', health, name='health'),
    path('', include(router.urls)),
]
