from django.db import models
from django.conf import settings

class LogSystem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null = True)
    action = models.CharField(max_length = 100)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length = 50)
    message = models.CharField(max_length = 100)

    def __str__(self):
        return f"{self.timestamp} | {self.user.username} |  | {self.action} | {self.status}"

    class Meta:
        db_table = 'Log_system'
