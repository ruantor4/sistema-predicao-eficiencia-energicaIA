from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from core.utils import report_log


class LoginView(View):

    def get(self, request: HttpRequest) -> HttpResponse:

        try:
            if request.user.is_authenticated:
                return render(request, 'core/home.html')

            return render(request, 'autenticacao/login.html')

        except Exception as e:
            messages.error(request, "Erro ao carregar a página de login.")
            report_log(request.user if request.user.is_authenticated else None, "Acessar Login",
                       "ERROR", f"Erro ao carregar página de login: {e}")
            return redirect('login')

    def post(self, request: HttpRequest) -> HttpResponse:

        try:
            username = request.POST.get('username')
            password = request.POST.get('password')

            usuario = authenticate(username=username, password=password)

            if usuario is not None:
                login(request, usuario)
                return render(request, 'core/home.html')
            else:
                messages.error(request, "Usuário ou senha incorretos.")
                return render(request, 'autenticacao/login.html')

        except Exception as e:
            report_log(request.user if request.user.is_authenticated else None, "Login",
                       "ERROR", f"Erro inesperado: {e}")
            messages.error(request, "Erro ao Efetuar Login.")
            return redirect('login')


class LogoutView(View):
    def get(self, request: HttpRequest) -> HttpResponse:
        try:
            username = request.user.username if request.user.is_authenticated else 'Usuário desconhecido'
            if request.user.is_authenticated:
                logout(request)
                messages.error(request, f'{username} fez logout com sucesso!.')
                return redirect('login')

        except Exception as e:
            report_log(request.user if request.user.is_authenticated else None, "Logout", "ERROR",
                       f"Erro inesperado: {e}")
            messages.error(request, "Erro inesperado ao encerrar a sessão.")
            return redirect('login')

