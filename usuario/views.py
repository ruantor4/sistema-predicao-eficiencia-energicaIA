from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views import View

from usuario.models import Usuario


class ListarUsuariosView(LoginRequiredMixin, View):
    def get(self, request):
        usuarios = Usuario.objects.all()
        return render(request, 'usuario/listar_usuarios.html', {'usuarios': usuarios})
