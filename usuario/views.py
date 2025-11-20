from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction, IntegrityError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from core.utils import report_log
from usuario.models import Usuario
from usuario.utils import validar_usuario, validar_senha


class ListarUsuariosView(LoginRequiredMixin, View):
    def get(self, request:HttpRequest) -> HttpResponse:
        try:
            usuarios = Usuario.objects.all()
            return render(request, 'usuario/listar_usuarios.html', {'usuarios': usuarios})

        except Exception as e:
            report_log(request.user if request.user.is_authenticated else None, "Listar Usuário", "ERROR",
                       f"Erro inesperado: {e}")
            messages.error(request, "Erro ao carregar usuários")
            return redirect('home')


class CriarUsuarioView(LoginRequiredMixin, View):
    def get(self, request:HttpRequest) -> HttpResponse:

        try:
            return render(request, 'usuario/form_usuario.html')

        except Exception as e:
            report_log(request.user if request.user.is_authenticated else None, "Criar Usuário", "ERROR",
                       f"Erro inesperado: {e}")
            messages.error(request, "Erro ao exibir página")
            return redirect('criar_usuario')


    def post(self, request:HttpRequest) -> HttpResponse:

        nome = request.POST.get("nome", '').strip()
        username = request.POST.get("username", '').strip()
        email = request.POST.get("email", '').strip()
        telefone = request.POST.get("telefone", '').strip()
        senha = request.POST.get("senha", '').strip()

        if not validar_usuario(request, username,email):
            return redirect('criar_usuario')

        if not validar_senha(request, senha):
            return redirect('criar_usuario')

        try:
            with transaction.atomic():
                Usuario.objects.create_user(
                    nome=nome,
                    username=username,
                    email=email,
                    telefone=telefone,
                    password=senha
                )
            messages.success(request, "Usuário criado com sucesso")
            return redirect('listar_usuarios')

        except IntegrityError:
            messages.error(request, "Erro de integridade no banco. Tente novamente.")
            return redirect('criar_usuario')

        except Exception as e:
            report_log(request.user if request.user.is_authenticated else None, "Criar Usuário", "ERROR",
                       f"Erro inesperado: {e}")
            messages.error(request, "Erro ao criar usuário.")
            return redirect('criar_usuarios')

class EditarUsuarioView(LoginRequiredMixin, View):
    def get(self, request:HttpRequest, usuario_id) -> HttpResponse:
        try:
            usuario = get_object_or_404(Usuario, id=usuario_id)
            return render(request, 'usuario/form_usuario.html', {'usuario': usuario})

        except Exception as e:
            report_log(request.user if request.user.is_authenticated else None, "Editar Usuário", "ERROR",
                       f"Erro inesperado: {e}")
            messages.error(request, "Erro inesperado")
            return redirect('listar_usuarios')

    def post(self, request:HttpRequest, usuario_id) -> HttpResponse:

        usuario = get_object_or_404(Usuario, id=usuario_id)
        nome = request.POST.get("nome", '').strip()
        username = request.POST.get("username", '').strip()
        email = request.POST.get("email", '').strip()
        telefone = request.POST.get("telefone", '').strip()
        senha = request.POST.get("senha", '').strip()

        if not validar_usuario(request, username,email, usuario_id=usuario_id):
            return redirect('editar_usuario', usuario_id=usuario_id)

        if senha and not validar_senha(request, senha):
            return redirect('editar_usuario', usuario_id=usuario_id)

        try:
            with transaction.atomic():
                usuario.nome = nome
                usuario.username = username
                usuario.email = email
                usuario.telefone = telefone

                if senha:
                    usuario.set_password(senha)
                    messages.success(request, f"Senha do usuario {usuario.username} atualizada com sucesso")
                usuario.save()

            messages.success(request, "Usuário atualizado com sucesso")
            return redirect('listar_usuarios')

        except Exception as e:
            report_log(request.user if request.user.is_authenticated else None, "Editar Usuário", "ERROR",
                       f"Erro inesperado: {e}")
            messages.error(request, "Erro ao atualizar Usuário")
            return redirect('editar_usuario', usuario_id=usuario_id)

class DeletarUsuarioView(LoginRequiredMixin, View):

    def get(self,request:HttpRequest, usuario_id) -> HttpResponse:
        try:
            usuario = get_object_or_404(Usuario, id=usuario_id)
            return render(request, 'usuario/confirm_del_usuario.html', {'usuario': usuario})
        except Exception as e:
            report_log(request.user if request.user.is_authenticated else None, "Deletar Usuario", "ERROR",
                       f"Erro inesperado: {e}")
            messages.error(request, "Erro inesperado")
            return redirect('listar_usuarios')

    def post(self, request:HttpRequest, usuario_id) -> HttpResponse:
        usuario = get_object_or_404(Usuario, id=usuario_id)

        if usuario.username.lower() == 'admin':
            messages.error(request, "O usuário 'admin' não pode ser excluído.")
            return redirect('listar_usuarios')

        if not request.user.is_superuser:
            messages.error(request, "Apenas superusuários podem excluir usuários.")
            return redirect('listar_usuarios')
        try:
            usuario.delete()
            messages.success(request, f"Usuário '{usuario.username}' deletado com sucesso.")
            return redirect('listar_usuarios')

        except Exception as e:
            report_log(request.user if request.user.is_authenticated else None, "Excluir Usuário", "ERROR",
                          f"Erro ao deletar usuário: {str(e)}")
            messages.error(request, "Erro ao excluir o usuário. Tente novamente mais tarde.")
        return redirect('listar_usuarios', usuario_id=usuario_id)