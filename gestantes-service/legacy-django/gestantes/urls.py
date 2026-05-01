from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GestanteViewSet, ConsentimentoGestanteViewSet

router = DefaultRouter()
router.register(r'gestantes', GestanteViewSet)
router.register(r'consentimentos', ConsentimentoGestanteViewSet)

urlpatterns = [
    path('', include(router.urls)),
]