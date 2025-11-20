from django.conf import settings
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

class SenhaResetView(View):

    def get(self, request: HttpRequest) -> HttpResponse:
        try:
            return render(request, 'autenticacao/reset_senha.html')

        except Exception as e:
            report_log(request.user if request.user.is_authenticated else None, "Reset Senha", "ERROR",
                       f"Erro inesperado: {e}")
            messages.error(request, "Não foi possivel carregar a página.")
            return redirect('login')

    def post(self, request: HttpRequest) -> HttpResponse:
        email = request.POST.get('email')

        try:
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            usuario = None

        except Exception as e:
            report_log(request.user if request.user.is_authenticated else None, "Reset Senha", "ERROR",
                       f"Erro ao enviar solicitação: {e}")
            messages.error(request, "Erro inesperado, tente novamente.")
            return redirect('login')

        if usuario:
            try:
                uid = urlsafe_base64_encode(force_bytes(usuario.pk))
                token = default_token_generator.make_token(usuario)
                reset_link = request.build_absolute_uri(
                    reverse('confirm_reset_senha', kwargs={'uidb64': uid, 'token': token})
                )

                subject = "Redefinição de senha"
                message = (
                        f"Olá, {usuario.nome},"
                        f"\n\nClique no link abaixo para redefinir sua senha:\n\n{reset_link}"
                        f"\n\nSe você não solicitou isso, ignore este e-mail."
                )
                send_mail(subject, message, None, [email])
                messages.success(request, "Um link de redefinição de senha foi enviado para seu e-mail.")
                return redirect('login')

            except Exception as e:
                report_log(request.user if request.user.is_authenticated else None, "Reset senha", "ERROR",
                               f"Erro inesperado: {e}")
                messages.error(request, "Erro inesperado, tente novamente.")
                return redirect('login')
        else:
            messages.warning(request, "Se o e-mail existir, enviaremos um link de redefinição.")
        return redirect('login')

class ConfirmarSenhaResetView(View):

    def get_user(self, uidb64):

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            return Usuario.objects.get(pk=uid)

        except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
            return None

        except Exception as e:
            report_log(None, "Reset de senha", "ERROR", f"Erro ao decodificar UID: {str(e)}")
            return None

    def get(self, request: HttpRequest, uidb64, token) -> HttpResponse:

        try:
            usuario = self.get_user(uidb64)

            if usuario is not None and default_token_generator.check_token(usuario, token):
                return render(request, 'autenticacao/confirm_reset_senha.html', {'usuario':Usuario})
            else:
                messages.error(request, "Link inválido ou expirou.")
                return redirect('login')

        except Exception as e:
            report_log(request.user if request.user.is_authenticated else None, "Confirmaçao de senha", "ERROR",
                       f"Erro na confirmação: {str(e)}")
            messages.error(request, "Erro na confirmação de reset.")
            return redirect('login')

    def post(self,request: HttpRequest, uidb64, token) -> HttpResponse:

        usuario = self.get_user(uidb64)
        if usuario is None or not default_token_generator.check_token(usuario, token):
            messages.error(request,"Link invalido ou expirou.")
            return redirect('login')

        senha1 = request.POST.get('senha1')
        senha2 = request.POST.get('senha2')

        if senha1 != senha2:
            messages.error(request, "As senhas nao coincidem.")
            return redirect(request.path)

        if len(senha1) < 6:
            messages.error(request, "A senha deve conter pelo menos 6 caracteres.")
            return redirect(request.path)

        try:
            usuario.set_password(senha1)
            usuario.save()
            messages.success(request, "Senha redefinida com sucesso.")
            return redirect('login')

        except Exception as e:
            report_log(request.user if request.user.is_authenticated else None, "Reset de senha", "ERROR",
                       f"Erro ao definir senha: {e}")
            messages.error(request, "Erro ao redefinir senha.")
        return redirect('login')



