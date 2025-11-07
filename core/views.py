from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View

from core.utils import report_log


class HomeView(LoginRequiredMixin, View):

    login_url = '/login/'

    def get(self, request:HttpRequest) -> HttpResponse:
        try:
            return render(request, 'core/home.html')

        except Exception as e:
            messages.error(request, 'Erro ao exibir página.')
            report_log(request.user if request.user.is_authenticated else None,
                       "Acessar Home", "ERROR", f"Erro ao carregar pagina {e}")
            return render(request, 'autenticacao/login.html')

