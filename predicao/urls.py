from django.urls import path

from predicao.views import CriarPredicaoView, ListarPredicoesView

urlpatterns = [
    path('criar/', CriarPredicaoView.as_view(), name='criar_predicao'),
    path('historico/', ListarPredicoesView.as_view(), name='listaar_predicoes'),
]
