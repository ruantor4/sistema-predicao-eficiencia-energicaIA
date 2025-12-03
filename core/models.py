from django.db import models
from django.conf import settings

class LogSystem(models.Model):
    """
    Model responsável por armazenar registros de operações realizadas no sistema.

    Este modelo é utilizado para guardar logs contendo informações importantes
    sobre ações executadas pelos usuários ou pelo próprio sistema, incluindo
    detalhes como o usuário envolvido, o tipo de ação, o status do processo
    e mensagens adicionais relevantes.

    Atributos
    ---------
    user : ForeignKey
        Referência ao usuário responsável pela ação.
        Pode ser nulo para registrar eventos do sistema ou ações anônimas.

    action : CharField
        Descrição curta da ação executada (ex.: 'Login', 'Reset de Senha', 'Erro').

    timestamp : DateTimeField
        Data e hora em que o evento foi registrado.
        Gerado automaticamente no momento da criação.

    status : CharField
        Indica o status da ação (ex.: 'SUCCESS', 'ERROR', 'WARNING').

    message : TextField
        Mensagem detalhada explicando o resultado da ação,
           útil para auditoria e análise de erros.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null = True)
    action = models.CharField(max_length = 255, verbose_name="Ação")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Data e Hora")
    status = models.CharField(max_length = 100, verbose_name="Status")
    message = models.TextField(verbose_name="Mensagem")

    def __str__(self):
        """
        Retorna uma representação legível do log,
        combinando data, usuário e ação registrada.
        """
        user = self.user.username if self.user else "Anônimo"
        return f"{self.timestamp} - {user} - {self.action}"

    class Meta:
        db_table = 'log_system'
        ordering = ['-timestamp']  # Logs mais recentes primeiro
        verbose_name = 'Log do Sistema'
        verbose_name_plural = 'Logs do Sistema'
