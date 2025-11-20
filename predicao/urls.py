from django.urls import path

from predicao.views import CriarPredicaoView

urlpatterns = [
    path('criar/', CriarPredicaoView.as_view(), name='criar_predicao'),
]
