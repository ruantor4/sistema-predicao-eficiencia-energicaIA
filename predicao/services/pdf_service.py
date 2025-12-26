from typing import Dict, List

from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

from predicao.models import Predicao


class PredicaoPDFService:
    """
    Serviço responsável por gerar o PDF do Dashboard de Predições.

    Responsabilidade:
    - Gerar um relatório PDF estático e confiável.
    - Consolidar estatísticas e histórico de predições.
    - Não conter lógica de negócio ou cálculos do modelo.
    """

    @staticmethod
    def gerar_pdf(
        response: HttpResponse,
        stats: Dict[str, float],
        registros: List[Predicao],
    ) -> None:
        """
        Monta e escreve o PDF diretamente na resposta HTTP.

        Estrutura do PDF:
        - Título do relatório
        - Estatísticas gerais do dashboard
        - Histórico detalhado das predições

        Args:
            response (HttpResponse):
                Objeto de resposta HTTP onde o PDF será escrito.
            stats (Dict[str, float]):
                Estatísticas já calculadas (total, máximos, medianas, etc).
            registros (List[Predicao]):
                Lista de predições ordenadas por data.
        """
        doc = SimpleDocTemplate(
            response,
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )

        styles = getSampleStyleSheet()
        elementos = []
        # ===== TÍTULO =====
        elementos.append(
            Paragraph("<b>Relatório Avançado de Predições</b>", styles["Title"])
        )
        elementos.append(Spacer(1, 0.6 * cm))

        # ===== ESTATÍSTICAS =====
        elementos.append(
            Paragraph("<b>Estatísticas Gerais</b>", styles["Heading2"])
        )
        elementos.append(Spacer(1, 0.3 * cm))

        for k, v in stats.items():
            elementos.append(
                Paragraph(f"{k}: <b>{v}</b>", styles["Normal"])
            )

        elementos.append(Spacer(1, 0.6 * cm))

        # ===== HISTÓRICO =====
        elementos.append(
            Paragraph("<b>Histórico de Predições</b>", styles["Heading2"])
        )
        elementos.append(Spacer(1, 0.3 * cm))

        for p in registros:
            elementos.append(
                Paragraph(
                    f"{p.data_criacao.strftime('%d/%m/%Y %H:%M')} "
                    f"| AQ: {p.carga_aquecimento} "
                    f"| RF: {p.carga_resfriamento} "
                    f"| Orientação: {p.orientacao}",
                    styles["Normal"],
                )
            )

        doc.build(elementos)