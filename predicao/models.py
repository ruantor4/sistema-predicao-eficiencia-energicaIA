from django.conf import settings
from django.db import models


class Predicao(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # VARIÁVEIS DE ENTRADA (em português)
    compacidade_relativa = models.FloatField(verbose_name="Compacidade Relativa")
    area_superficial = models.FloatField(verbose_name="Área Superficial")
    area_paredes = models.FloatField(verbose_name="Área das Paredes")
    area_teto = models.FloatField(verbose_name="Área do Teto")
    altura_total = models.FloatField(verbose_name="Altura Total")
    orientacao = models.IntegerField(verbose_name="Orientação")
    area_vidros = models.FloatField(verbose_name="Área de Vidros")
    distribuicao_vidros = models.IntegerField(verbose_name="Distribuição da Área de Vidros")

    # RESULTADOS (também em português)
    carga_aquecimento = models.FloatField(verbose_name="Carga de Aquecimento")
    carga_resfriamento = models.FloatField(verbose_name="Carga de Resfriamento")

    data_criacao = models.DateTimeField(auto_now_add=True, verbose_name="Data da Predição")

    def __str__(self) -> str:
        return f"Predição #{self.pk} - Usuário: {getattr(self.usuario, 'username', 'desconhecido')}"

    class Meta:
        db_table = 'predicao'
        ordering = ["-data_criacao"]