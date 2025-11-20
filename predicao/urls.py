from django.urls import path

from predicao.views import CriarPredicaoView, ListarPredicoesView, ExcluirPredicaoView

urlpatterns = [
    path('criar/', CriarPredicaoView.as_view(), name='criar_predicao'),
    path('historico/', ListarPredicoesView.as_view(), name='listar_predicoes'),
    path("excluir/<int:pk>/", ExcluirPredicaoView.as_view(), name="excluir_predicao"),
]
