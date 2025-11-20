from django.urls import path

from usuario.views import ListarUsuariosView, CriarUsuarioView, EditarUsuarioView, DeletarUsuarioView

urlpatterns = [
    path('', ListarUsuariosView.as_view() , name='listar_usuarios'),

    path('criar/', CriarUsuarioView.as_view(), name='criar_usuario'),

    path('editar/<int:usuario_id>', EditarUsuarioView.as_view(), name='editar_usuario'),

    path('deletar/<int:usuario_id>', DeletarUsuarioView.as_view(), name='deletar_usuario'),
]
