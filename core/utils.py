from django.contrib.auth.models import User

from core.models import LogSystem


def report_log(user: User, action: str, status: str, message: str):

    LogSystem.objects.create(
        user=user,
        action=action,
        status=status,
        message=message
    )