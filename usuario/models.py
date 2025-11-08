from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):

    nome = models.CharField('Nome Completo', max_length=255)
    telefone = models.CharField('Telefone', max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nome or self.username

    class Meta:
        db_table = 'usuario'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'