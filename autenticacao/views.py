
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View

from core.utils import report_log
from usuario.models import Usuario


class LoginView(View):
    """
    Classe responsável por gerenciar as operações de exibição e autenticação
    relacionadas à tela de login do sistema. Esta view implementa os métodos
    GET e POST, tratando exibição condicional, autenticação, mensagens ao
    usuário e registro de logs de operação e erro.

    Métodos
    -------
    get(request: HttpRequest) -> HttpResponse
        Exibe a página de login ou redireciona o usuário caso já esteja autenticado.

    post(request: HttpRequest) -> HttpResponse
        Processa o envio do formulário de login, validando credenciais e gerando
        respostas apropriadas com tratamento de erro e logging.
    """
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Manipula requisições HTTP GET para a página de login.

        Este método verifica se o usuário já está autenticado. Caso esteja,
        redireciona diretamente para a página inicial. Caso contrário,
        exibe a interface de login. Em situações de erro inesperado,
        registra o evento e retorna o usuário à rota de login.

        Parâmetros
        ----------
        request : HttpRequest
            Objeto contendo os dados da requisição HTTP, incluindo informações
            da sessão e do usuário logado (se existir).

        Retorno
        -------
        HttpResponse
            Página renderizada correspondente ao estado do usuário ou redirecionamento
            em caso de erro.
        """
        try:
            # Usuário autenticado → enviar para a página inicial
            if request.user.is_authenticated:
                return render(request, 'core/home.html')

            # Usuário não autenticado → exibir tela de login
            return render(request, 'autenticacao/login.html')

        except Exception as e:
            messages.error(request, "Erro ao carregar a página de login.")
            report_log(
                request.user if request.user.is_authenticated else None,
                "Acessar Login",
                "ERROR",
                f"Erro ao carregar página de login: {e}"
            )
            return redirect('login')

    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Manipula requisições HTTP POST para o processo de autenticação.

        Este método recebe os dados enviados pelo formulário, valida as
        credenciais do usuário e realiza o processo de autenticação com os
        mecanismos nativos do framework. Retorna a página inicial caso o
        login seja bem-sucedido ou mantém o usuário na tela de login em
        caso de falha. Em situações de erro inesperado, registra o log
        e redireciona novamente à página de login.

        Parâmetros
        ----------
        request : HttpRequest
            Objeto da requisição contendo os dados enviados via formulário,
            como nome de usuário e senha.

        Retorno
        -------
        HttpResponse
            Página inicial após autenticação bem-sucedida ou retorno à
            página de login com mensagem de erro.
        """
        try:
            # Coleta de credenciais do formulário
            username = request.POST.get('username')
            password = request.POST.get('password')

            # Validação e autenticação do usuário
            usuario = authenticate(username=username, password=password)

            if usuario is not None:
                login(request, usuario)
                return render(request, 'core/home.html')
            else:
                messages.error(request, "Usuário ou senha incorretos.")
                return render(request, 'autenticacao/login.html')

        except Exception as e:
            report_log(
                request.user if request.user.is_authenticated else None,
                "Login",
                "ERROR",
                f"Erro inesperado: {e}"
            )
            messages.error(request, "Erro ao Efetuar Login.")
            return redirect('login')


class LogoutView(View):
    """
    Classe responsável por gerenciar a operação de logout do usuário.
    Realiza o encerramento seguro da sessão, registra o evento e
    redireciona de forma adequada após a finalização do processo.

    Métodos
    -------
    get(request: HttpRequest) -> HttpResponse
        Finaliza a sessão atual, exibe uma mensagem ao usuário e o redireciona.
    """
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Manipula requisições HTTP GET para o processo de logout.

        Este método verifica se o usuário está autenticado. Se estiver,
        encerra sua sessão, exibe uma mensagem e redireciona para a página inicial.
        Em caso de falha inesperada, o erro é registrado e o usuário também
        é redirecionado.

        Parâmetros
        ----------
        request : HttpRequest
            Objeto contendo dados da requisição e informações da sessão.

        Retorno
        -------
        HttpResponse
            Redirecionamento para a página inicial.
        """
        try:
            # Efetua logout apenas se o usuário estiver autenticado
            if request.user.is_authenticated:
                username = request.user.username
                logout(request)
                messages.success(request, f'{username} fez logout com sucesso!.')
                return redirect('home')

            return redirect('home')

        except Exception as e:
            report_log(
                request.user if request.user.is_authenticated else None,
                    "Logout",
                    "ERROR",
                    f"Erro inesperado: {e}"
            )
            messages.error(request, "Erro inesperado ao encerrar a sessão.")
            return redirect('home')


class SenhaResetView(View):
    """
    Classe responsável por iniciar o processo de redefinição de senha.
    Permite que o usuário informe seu e-mail para receber um link de
    redefinição, incluindo validações e tratamento de exceções.

    Métodos
    -------
    get(request: HttpRequest) -> HttpResponse
        Exibe o formulário de solicitação de redefinição de senha.

    post(request: HttpRequest) -> HttpResponse
        Processa o envio do formulário e envia o e-mail com o link de redefinição.
    """
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Exibe a página de solicitação de redefinição de senha.

        Parâmetros
        ----------
        request : HttpRequest
            Requisição recebida pelo servidor.

        Retorno
        -------
        HttpResponse
            Página com o formulário de recuperação de senha.
        """
        try:
            return render(request, 'autenticacao/reset_senha.html')

        except Exception as e:
            report_log(
                request.user if request.user.is_authenticated else None,
                    "Reset Senha",
                    "ERROR",
                    f"Erro inesperado: {e}"
            )
            messages.error(request, "Não foi possível carregar a página.")
            return redirect('login')

    def post(self, request: HttpRequest) -> HttpResponse:
        """
        Processa o envio do formulário de redefinição de senha.

        Este método valida se existe um usuário com o e-mail informado
        e, caso exista, envia um e-mail contendo um link seguro de
        redefinição de senha. Sempre retorna uma resposta genérica
        por segurança.

        Parâmetros
        ----------
        request : HttpRequest
            Requisição contendo o e-mail informado pelo usuário.

        Retorno
        -------
        HttpResponse
            Redirecionamento para a página de login com mensagem apropriada.
        """
        email = request.POST.get('email')

        try:
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            usuario = None

        except Exception as e:
            report_log(
                request.user if request.user.is_authenticated else None,
                    "Reset Senha",
                    "ERROR",
                    f"Erro ao enviar solicitação: {e}"
            )
            messages.error(request, "Erro inesperado, tente novamente.")
            return redirect('login')

        if usuario:
            try:
                # Gerar identificador seguro
                uid = urlsafe_base64_encode(force_bytes(usuario.pk))

                # Gerar token único
                token = default_token_generator.make_token(usuario)

                # Construir link absoluto de redefinição
                reset_link = request.build_absolute_uri(
                    reverse('confirm_reset_senha', kwargs={'uidb64': uid, 'token': token})
                )

                # Criar mensagem
                subject = "Redefinição de senha"
                message = (
                        f"Olá, {usuario.nome},"
                        f"\n\nClique no link abaixo para redefinir sua senha:\n\n{reset_link}"
                        f"\n\nSe você não solicitou isso, ignore este e-mail."
                )

                # Enviar e-mail
                send_mail(subject, message, None, [email])
                messages.success(request, "Um link de redefinição de senha foi enviado para seu e-mail.")
                return redirect('login')

            except Exception as e:
                report_log(
                    request.user if request.user.is_authenticated else None,
                        "Reset senha",
                        "ERROR",
                        f"Erro inesperado: {e}"
                )
                messages.error(request, "Erro inesperado, tente novamente.")
                return redirect('login')
        else:
            messages.warning(request, "Se o e-mail existir, enviaremos um link de redefinição.")
        return redirect('login')


class ConfirmarSenhaResetView(View):
    """
    Classe responsável por confirmar o link de redefinição e permitir
    que o usuário defina sua nova senha após validar token e identificador.

    Métodos
    -------
    get_user(uidb64)
        Decodifica e retorna o usuário correspondente ao UID.

    get(request, uidb64, token) -> HttpResponse
        Exibe o formulário de redefinição caso o link seja válido.

    post(request, uidb64, token) -> HttpResponse
        Valida a nova senha, atualiza o registro e finaliza o processo.
    """

    def get_user(self, uidb64):
        """
        Obtém um usuário a partir de um UID codificado.

        Parâmetros
        ----------
        uidb64 : str
            Identificador codificado do usuário.

        Retorno
        -------
        Usuario | None
            Retorna o usuário correspondente ou None se inválido.
        """
        try:
            # Decodifica o identificador
            uid = force_str(urlsafe_base64_decode(uidb64))
            return Usuario.objects.get(pk=uid)

        except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
            return None

        except Exception as e:
            report_log(
                None, "Reset de senha", "ERROR", f"Erro ao decodificar UID: {str(e)}"
            )
            return None

    def get(self, request: HttpRequest, uidb64, token) -> HttpResponse:
        """
        Exibe o formulário de redefinição de senha caso o link seja válido.

        Parâmetros
        ----------
        request : HttpRequest
            Requisição recebida.
        uidb64 : str
            Identificador do usuário.
        token : str
            Token de validação.

        Retorno
        -------
        HttpResponse
            Formulário de redefinição ou redirecionamento para login.
        """
        try:
            usuario = self.get_user(uidb64)

            # Verifica token e usuário
            if usuario is not None and default_token_generator.check_token(usuario, token):
                return render(request, 'autenticacao/confirm_reset_senha.html', {'usuario': usuario})
            else:
                messages.error(request, "Link inválido ou expirou.")
                return redirect('login')

        except Exception as e:
            report_log(
                request.user if request.user.is_authenticated else None,
                "Confirmaçao de senha",
                "ERROR",
                f"Erro na confirmação: {str(e)}"
            )
            messages.error(request, "Erro na confirmação de reset.")
            return redirect('login')

    def post(self,request: HttpRequest, uidb64, token) -> HttpResponse:
        """
        Processa o envio do formulário e define a nova senha do usuário.

        Parâmetros
        ----------
        request : HttpRequest
            Dados enviados pelo formulário.
        uidb64 : str
            Identificador codificado do usuário.
        token : str
            Token que valida o processo.

        Retorno
        -------
        HttpResponse
            Redirecionamento após redefinir senha ou aviso de erro.
        """
        usuario = self.get_user(uidb64)

        # Verificar validade do link
        if usuario is None or not default_token_generator.check_token(usuario, token):
            messages.error(request,"Link inválido ou expirou.")
            return redirect('login')

        senha1 = request.POST.get('senha1')
        senha2 = request.POST.get('senha2')

        # Validar igualdade das senhas
        if senha1 != senha2:
            messages.error(request, "As senhas não coincidem.")
            return redirect(request.path)

        # Mínimo de segurança
        if len(senha1) < 6:
            messages.error(request, "A senha deve conter pelo menos 6 caracteres.")
            return redirect(request.path)

        try:
            # Atualizar senha
            usuario.set_password(senha1)
            usuario.save()
            messages.success(request, "Senha redefinida com sucesso.")
            return redirect('login')

        except Exception as e:
            report_log(
                request.user if request.user.is_authenticated else None,
                "Reset de senha",
                "ERROR",
                f"Erro ao definir senha: {e}"
            )
            messages.error(request, "Erro ao redefinir senha.")
            return redirect('login')



