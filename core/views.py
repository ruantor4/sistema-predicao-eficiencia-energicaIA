from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import View

from core.utils import report_log


class HomeView(View):
    """
    View responsável por exibir a página inicial do sistema.

    Esta classe lida com requisições GET encaminhando o usuário
    para a página principal. Em caso de erro inesperado, registra
    o evento no sistema de logs e retorna a página de login
    com mensagem apropriada.

    Atributos
    ---------
    login_url : str
        URL de login utilizada como referência para redirecionamentos
        ou validações internas quando necessário.

    Métodos
    -------
    get(request: HttpRequest) -> HttpResponse
        Processa requisições GET, renderizando a página inicial ou
        exibindo fallback de erro caso ocorra uma exceção.
    """
    login_url = '/login/'

    def get(self, request:HttpRequest) -> HttpResponse:
        """
        Manipula requisições HTTP GET para exibição da página inicial.

        Este método é responsável por renderizar o template principal
        do sistema. Caso ocorra qualquer exceção durante o processo
        de renderização, o erro será registrado no sistema de logs
        e o usuário receberá uma mensagem informativa, sendo
        direcionado para a tela de login.

        Parâmetros
        ----------
        request : HttpRequest
            Objeto que contém os dados da requisição HTTP, incluindo
            informações de sessão e autenticação do usuário.

        Retorno
        -------
        HttpResponse
            A página inicial renderizada em caso de sucesso, ou a
            página de login em caso de erro durante o processamento.
        """
        try:
            # Renderiza a página principal
            return render(request, 'core/home.html')

        except Exception as e:
            messages.error(request, 'Erro ao exibir página.')
            report_log(
                request.user if request.user.is_authenticated else None,
                "Acessar Home",
                "ERROR",
                f"Erro ao carregar pagina {e}"
            )
            return render(request, 'autenticacao/login.html')

