
from django.urls import path

from autenticacao.views import LoginView, LogoutView

urlpatterns = [

    # Rota para Login
    path('', LoginView.as_view(), name='login'),

    path('logout/', LogoutView.as_view(), name='logout'),


]
