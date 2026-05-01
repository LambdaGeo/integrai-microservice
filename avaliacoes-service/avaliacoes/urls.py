from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AvaliacaoViewSet, PilulaViewSet

router = DefaultRouter()
router.register(r'avaliacoes', AvaliacaoViewSet)
router.register(r'pilulas', PilulaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]