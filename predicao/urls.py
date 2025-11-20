from django.urls import path

from predicao.dashbord_views import DashboadPredicaoView, PredicaoPDFView
from predicao.views import CriarPredicaoView, ListarPredicoesView, ExcluirPredicaoView

urlpatterns = [
    path('criar/', CriarPredicaoView.as_view(), name='criar_predicao'),
    path('historico/', ListarPredicoesView.as_view(), name='listar_predicoes'),
    path('excluir/<int:pk>/', ExcluirPredicaoView.as_view(), name="excluir_predicao"),

    path('dashboard/', DashboadPredicaoView.as_view(), name='dashboard_predicao'),
    path("dashboard/pdf/", PredicaoPDFView.as_view(), name="pdf_predicoes"),
]
