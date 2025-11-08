from django.contrib import messages
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from core.utils import report_log
from usuario.models import Usuario


def validar_usuario(request, username: str, email: str) -> bool:
    try:
        username = username.strip()
        email = email.strip().lower()

        if not username or not email:
            messages.error(request, "Todos os campos são obrigatórios.")
            return False

        if Usuario.objects.filter(username=username).exists():
            messages.error(request, "Já existe um usuário com este nome.")
            return False

        if Usuario.objects.filter(email=email).exists():
            messages.error(request, "Este e-mail já está em uso.")
            return False

        validate_email(email)

    except ValidationError:
        messages.error(request, "Endereço de e-mail inválido.")
        return False

    except Exception as e:
        report_log(request.user, "Validação criar usuarios", "ERROR", f"Erro inesperado: {str(e)}")
        messages.error(request, f"Erro inesperado: {str(e)}")
        return False

    return True


def validar_senha(request, senha: str) -> bool:
    try:
        if not senha:
            return True  # Se o campo estiver vazio, não obriga trocar a senha

        if len(senha) < 6:
            messages.warning(request, " A senha deve ter pelo menos 6 caracteres.")
            return False

    except ValidationError:
        messages.error(request, "erro na validação, tente novamente.")
        return False

    except Exception as e:
        report_log(request.user if request.user.is_authenticated else None, "validar senha", "ERROR", f"Erro inesperado: {str(e)}")
        messages.error(request, f"Erro inesperado: {str(e)}")
        return False

    return True

