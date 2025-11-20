from django.db import models
from django.conf import settings

class LogSystem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null = True)
    action = models.CharField(max_length = 255)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length = 100)
    message = models.TextField()

    def __str__(self):
        user = self.user.username if self.user else "Anônimo"
        return f"{self.timestamp} - {user} - {self.action}"

    class Meta:
        db_table = 'Log_system'
