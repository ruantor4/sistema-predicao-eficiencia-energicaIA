
from django.urls import path

from autenticacao.views import LoginView, LogoutView, SenhaResetView, ConfirmarSenhaResetView

urlpatterns = [

    # Rota para Login
    path('login/', LoginView.as_view(), name='login'),

    path('logout/', LogoutView.as_view(), name='logout'),

    path('reset_senha/', SenhaResetView.as_view(), name='reset_senha'),

    path('reset_senha/<uidb64>/<token>/', ConfirmarSenhaResetView.as_view(), name='confirm_reset_senha')
]
