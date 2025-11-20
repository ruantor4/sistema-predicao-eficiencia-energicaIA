from django.contrib.auth.models import User, AnonymousUser

from core.models import LogSystem


def report_log(user: User, action: str, status: str, message: str):

    if isinstance(User, AnonymousUser):
        user = None

    LogSystem.objects.create(
        user=user,
        action=action,
        status=status,
        message=message
    )