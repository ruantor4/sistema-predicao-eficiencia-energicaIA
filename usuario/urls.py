from django.urls import path

from usuario.views import ListarUsuariosView

urlpatterns = [
    path('', ListarUsuariosView.as_view() , name='listar_usuarios'),
]
