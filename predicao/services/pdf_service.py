from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm


class PredicaoPDFService:
    """
    Serviço responsável por gerar o PDF do Dashboard de Predições.

    Este serviço centraliza:
    - Formatação do PDF
    - Organização visual
    - Estilização consistente
    - Separação da responsabilidade (SRP)
    """

    @staticmethod
    def gerar_pdf(response, stats: dict, registros: list):
        """
        Monta e escreve o PDF diretamente na resposta HTTP.

        Args:
            response (HttpResponse): Objeto HTTP contendo o stream do PDF.
            stats (dict): Dados estatísticos do dashboard.
            registros (list): Lista de registros de predição.
        """
        doc = SimpleDocTemplate(response, pagesize=A4)
        styles = getSampleStyleSheet()
        elementos = []

        # ======= TÍTULO =======
        elementos.append(Paragraph("<b>Relatório Avançado de Predições</b>", styles["Title"]))
        elementos.append(Spacer(1, 0.7 * cm))

        # ======= ESTATÍSTICAS =======
        elementos.append(Paragraph("<b>Estatísticas Gerais</b>", styles["Heading2"]))
        elementos.append(Spacer(1, 0.2 * cm))

        for titulo, valor in stats.items():
            elementos.append(Paragraph(f"{titulo}: <b>{valor}</b>", styles["Normal"]))

        elementos.append(Spacer(1, 0.7 * cm))

        # ======= DETALHES POR REGISTRO =======
        elementos.append(Paragraph("<b>Predições Individuais</b>", styles["Heading2"]))
        elementos.append(Spacer(1, 0.2 * cm))

        for p in registros:
            elementos.append(Paragraph(
                f"- {p.data_criacao.strftime('%d/%m/%Y %H:%M')} "
                f"| Aq: {p.carga_aquecimento} "
                f"| Rsf: {p.carga_resfriamento} "
                f"| Orientação: {p.orientacao}",
                styles["Normal"]
            ))

        doc.build(elementos)
