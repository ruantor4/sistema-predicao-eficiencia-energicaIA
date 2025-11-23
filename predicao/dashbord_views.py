import io
from statistics import stdev, median, mean
from typing import Dict, List, Any
import pandas as pd
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect
from django.views import View
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
import matplotlib.pyplot as plt
from core.utils import report_log
from predicao.models import Predicao
from predicao.services.insights_service import gerar_insights_basicos, gerar_insights_preditivos
from predicao.model_loader import model, scaler


class DashboadPredicaoView(LoginRequiredMixin, View):
    """
    Classe responsável por renderizar o Dashboard Avançado de Predições do usuário.

    Esta view centraliza:
    - Coleta dos dados históricos do modelo (Predicao)
    - Processamento estatístico (maior, menor, mediana, desvios)
    - Preparação dos dados para gráficos (linha, barras, dispersão)
    - Geração de insights automáticos
    - Geração de insights preditivos vindos do modelo ML
    - Organização e entrega dos dados para o template HTML

    Atributos herdados:
        - LoginRequiredMixin:
            Garante que apenas usuários autenticados consigam acessar a view.
        - View:
            Permite implementação dos métodos HTTP (GET).

    Observação:
        Esta classe mantém consistência com o fluxo do PDF (PredicaoPDFView),
        utilizando a mesma lógica de cálculos e a mesma função interna de
        insights preditivos, garantindo que Dashboard e PDF nunca entrem em
        contradição.
    """

    @staticmethod
    def _safe_gerar_insight_preditivo(context: Dict[str, Any]) -> str:
        """
        Gera um insight preditivo chamando o modelo ML, garantindo segurança
        quanto ao formato dos dados enviados ao scaler, evitando warnings do sklearn.

        Esta função foi criada para:
            1. Eliminar warnings sobre `feature_names_in_` do StandardScaler.
            2. Garantir que mesmo inputs incompletos gerem um insight coerente.
            3. Manter o Dashboard alinhado com o PDF (usa mesma função).

        Processo Interno:
            1. Recupera a lista esperada de features do scaler.
            2. Constrói um DataFrame com colunas exatamente iguais às do scaler,
               mesmo que os dados venham parcialmente do contexto.
            3. Chama o gerador de insights preditivos.
            4. Normaliza o retorno (string ou lista → sempre string).
            5. Em caso de erro, retorna fallback sem travar o dashboard.

        Args:
            context (Dict[str, Any]):
                Dicionário contendo informações relevantes para geração do insight.
                Exemplos de chaves:
                    - "trend": tendência temporal
                    - "orientacao_max": orientação dominante
                    - "corr": correlação numérica
                    - "summary": dados agregados

        Returns:
            str:
                Insight preditivo formatado em texto simples.
                Nunca retorna None e nunca lança erro (tratamento completo).
        """
        try:
            expected_cols = getattr(scaler, "feature_names_in_", list(context.keys()))
            df_context = pd.DataFrame([context], columns=expected_cols)

            insight = gerar_insights_preditivos(model, scaler, df_context)

            if isinstance(insight, list):
                return insight[0] if insight else "Insight preditivo: sem retorno do modelo."
            if isinstance(insight, str):
                return insight

            return "Insight preditivo: formato inesperado retornado pelo gerador."

        except Exception:
            if "trend" in context:
                return f"Insight preditivo (fallback): tendência atual é '{context['trend']}'."
            if "orientacao_max" in context:
                return f"Insight preditivo (fallback): orientação com maior média é {context['orientacao_max']}."
            if "corr" in context:
                return f"Insight preditivo (fallback): correlação estimada = {context['corr']:.2f}."
            return "Insight preditivo (fallback): não foi possível gerar insight do modelo."


    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Método GET responsável por montar todo o dashboard de predições.

        Este método realiza:
            1. Carregamento das predições do usuário autenticado.
            2. Construção das séries temporais usadas nos gráficos.
            3. Cálculos estatísticos essenciais (maior, menor, mediana, desvio).
            4. Processamento das médias por orientação.
            5. Geração das estruturas de pontos de dispersão para gráficos scatter.
            6. Cálculo dos três tipos de insight automático:
                - Tendência temporal
                - Maior média por orientação
                - Correlação entre variáveis
            7. Geração dos insights preditivos usando o modelo ML.
            8. Repack final de todos os dados para serem enviados ao template.

        Fluxo detalhado:
            - Em caso de não haver predições, redireciona o usuário
                para criar sua primeira predição.
            - Todos os cálculos seguem o mesmo padrão da versão em PDF,
                garantindo consistência visual e estatística.
            - Possui tratamento de exceção global, evitando que erros quebrem
                o dashboard e registrando log técnico via report_log().

        Args:
            request (HttpRequest):
                Objeto contendo informações da requisição HTTP do usuário.

        Returns:
            HttpResponse:
                Resposta HTML renderizada com todos os dados estruturados
                para o template do dashboard (`predicao/dashboard.html`).
        """
        try:
            predicoes = Predicao.objects.filter(usuario=request.user).order_by("data_criacao")

            if not predicoes.exists():
                messages.info(request, "Nenhuma predição foi encontrada para gerar o dashboard.")
                return redirect("criar_predicao")

            # DADOS BÁSICOS PARA GRÁFICOS DE LINHA
            labels = [p.data_criacao.strftime("%d/%m") for p in predicoes]
            aq_vals = [p.carga_aquecimento for p in predicoes]
            rf_vals = [p.carga_resfriamento for p in predicoes]

            # CÁLCULOS ESTATÍSTICOS
            total = len(predicoes)
            maior_aq = round(max(aq_vals), 2)
            menor_resf = round(min(rf_vals), 2)
            desvio_padrao = round(stdev(aq_vals), 2) if total > 1 else 0
            mediana_geral = round(median(aq_vals + rf_vals), 2)

            # MÉDIAS POR ORIENTAÇÃO
            orient = {}
            for p in predicoes:
                orient.setdefault(p.orientacao, []).append(p.carga_resfriamento)

            orient_labels = list(orient.keys())
            orient_means = [mean(v) for v in orient.values()] if orient else []

            # SCATTER PLOTS (PONTOS DE DISPERSÃO)
            scatter_aq = [{"x": p.altura_total, "y": p.carga_aquecimento} for p in predicoes]
            scatter_resf = [{"x": p.area_superficial, "y": p.carga_resfriamento} for p in predicoes]

            # INSIGHT 1 — TENDÊNCIA TEMPORAL
            def _calc_trend(vals):
                if len(vals) < 4:
                    return "amostras insuficientes para tendência confiável"
                head = mean(vals[:3])           # média inicial
                tail = mean(vals[-3:])          # média final

                # Define tendência com tolerância de 5%
                if tail > head * 1.05:
                    return "tendência de alta"
                if tail < head * 0.95:
                    return "tendência de queda"
                return "tendência estável"

            trend_aq = _calc_trend(aq_vals)
            trend_rf = _calc_trend(rf_vals)
            insight1_auto = f"Aquecimento: {trend_aq}. Resfriamento: {trend_rf}."

            # Cria contexto para insight preditivo
            context1 = {
                "type": "temporal",
                "trend": {"aquecimento": trend_aq, "resfriamento": trend_rf},
                "last_values": {"aquecimento": aq_vals[-3:], "resfriamento": rf_vals[-3:]},
            }
            insight1_pred = self._safe_gerar_insight_preditivo(context1)

            # INSIGHT 2 — MÉDIA DE RESFRIAMENTO POR ORIENTAÇÃO
            if orient:
                max_orient = orient_labels[orient_means.index(max(orient_means))]
                insight2_auto = (
                    f"Orientação com maior média de resfriamento: {max_orient} "
                    f"(média = {max(orient_means):.2f})."
                )
            else:
                max_orient = None
                insight2_auto = "Sem dados por orientação."

            context2 = {
                "type": "orientacao",
                "orientacao_max": max_orient,
                "orientacao_medias": {k: mean(v) for k, v in orient.items()},
            }
            insight2_pred = self._safe_gerar_insight_preditivo(context2)

            # INSIGHT 3 — CORRELAÇÃO ENTRE ALTURA E AQUECIMENTO
            def _pearson(x, y):
                # Calcula correlação Pearson manualmente
                if len(x) < 2:
                    return 0.0

                mx, my = mean(x), mean(y)
                num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
                den_x = (sum((xi - mx) ** 2 for xi in x)) ** 0.5
                den_y = (sum((yi - my) ** 2 for yi in y)) ** 0.5

                if den_x * den_y == 0:
                    return 0.0
                return num / (den_x * den_y)

            alturas = [p.altura_total for p in predicoes]
            corr = _pearson(alturas, aq_vals)
            insight3_auto = f"Correlação estimada (altura vs aquecimento): {corr:.2f}."

            context3 = {
                "type": "scatter",
                "corr": corr,
                "summary": {
                    "altura_mean": mean(alturas) if alturas else None,
                    "aq_mean": mean(aq_vals) if aq_vals else None,
                },
            }
            insight3_pred = self._safe_gerar_insight_preditivo(context3)

            # INSIGHT 4 — CORRELAÇÃO ENTRE ÁREA E RESFRIAMENTO
            areas = [p.area_superficial for p in predicoes]
            corr_rf = _pearson(areas, rf_vals)

            insight4_auto = f"Correlação estimada (área vs resfriamento): {corr_rf:.2f}."

            context4 = {
                "type": "scatter_resf",
                "corr": corr_rf,
                "summary": {
                    "area_mean": mean(areas) if areas else None,
                    "rf_mean": mean(rf_vals) if rf_vals else None,
                },
            }

            insight4_pred = self._safe_gerar_insight_preditivo(context4)

            # RETORNO FINAL PARA O TEMPLATE
            return render(request, "predicao/dashboard.html", {
                "labels": labels,
                "aquecimento": aq_vals,
                "resfriamento": rf_vals,

                "total": total,
                "maior_aq": maior_aq,
                "menor_resf": menor_resf,
                "desvio_padrao": desvio_padrao,
                "mediana_geral": mediana_geral,

                "orientacoes_labels": orient_labels,
                "orientacoes_medias": orient_means,

                "scatter_aq": scatter_aq,
                "scatter_resf": scatter_resf,

                # INSIGHTS DO GRÁFICO 1
                "insight1_auto": insight1_auto,
                "insight1_pred": insight1_pred,

                # INSIGHTS DO GRÁFICO 2
                "insight2_auto": insight2_auto,
                "insight2_pred": insight2_pred,

                # INSIGHTS DO GRÁFICO 3
                "insight3_auto": insight3_auto,
                "insight3_pred": insight3_pred,

                # INSIGHTS DO GRAFICO 4
                "insight4_pred": insight4_pred,
                "insight4_auto": insight4_auto,
            })

        except Exception as e:
            report_log(request.user, "Dashboard Predições", "ERROR", f"Erro ao carregar dashboard: {e}")
            messages.error(request, "Erro ao carregar o dashboard.")
            return redirect("home")

class PredicaoPDFView(View):
    """
    Classe responsável pela geração e download do PDF contendo o relatório
    avançado de predições do usuário.

    Esta view executa:
        - Coleta dos dados do usuário autenticado
        - Cálculos estatísticos essenciais
        - Geração dos gráficos usando matplotlib
        - Inserção dos gráficos dentro do PDF (via ReportLab)
        - Geração dos insights automáticos e preditivos
        - Montagem completa das páginas do relatório

    Objetivo:
        Entregar um PDF profissional, consistente com as informações vistas
        no dashboard, garantindo total correspondência entre as análises
        visuais e numéricas.

    Observação:
        Toda a lógica de insights é coerente com a view do dashboard,
        garantindo consistência de resultados.
    """
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Método GET responsável por iniciar a geração do PDF.

        Fluxo detalhado:
            1. Carrega todas as predições do usuário.
            2. Se não houver predições, exibe aviso e redireciona.
            3. Calcula estatísticas primárias usadas na capa do PDF.
            4. Cria a resposta HTTP com MIME type de PDF.
            5. Chama o método gerar_pdf() para montar todas as páginas.
            6. Retorna o PDF final pronto para download.

        Args:
            request (HttpRequest):
                Requisição HTTP do usuário autenticado.

        Returns:
            HttpResponse:
                PDF final gerado contendo gráficos, insights e histórico.
        """
        try:
            predicoes = Predicao.objects.filter(
                usuario=request.user
            ).order_by("data_criacao")

            if not predicoes.exists():
                messages.info(request, "Nenhuma predição disponível para gerar PDF.")
                return redirect("dashboard_predicao")

            # Extrai valores essenciais para cálculos estatísticos
            aquecimento = [p.carga_aquecimento for p in predicoes]
            resfriamento = [p.carga_resfriamento for p in predicoes]

            # Cálculos estatísticos básicos para a primeira página
            stats = {
                "Total de Predições": predicoes.count(),
                "Maior Aquecimento": round(max(aquecimento), 2),
                "Menor Resfriamento": round(min(resfriamento), 2),
                "Desvio Padrão (Aquecimento)": round(stdev(aquecimento), 2) if len(aquecimento) > 1 else 0,
                "Mediana Geral": round(median(aquecimento + resfriamento), 2),
            }

            # Cria a resposta HTTP no formato PDF
            response = HttpResponse(content_type="application/pdf")
            response["Content-Disposition"] = "attachment; filename=dashboard_predicoes.pdf"

            # Chama o método responsável por renderizar todas as páginas

            self.gerar_pdf(response, stats, predicoes)

            return response

        except Exception as e:
            report_log(request.user, "PDF Predições", "ERROR", f"Erro ao gerar PDF: {e}")
            messages.error(request, "Erro ao gerar o PDF das predições.")
            return redirect("dashboard_predicao")

    @staticmethod
    def _safe_gerar_insight_preditivo(context: Dict[str, Any]) -> str:
        """
        Gera insight preditivo com tratamento seguro e compatível com o scaler.

        Esta função garante:
            - Correspondência entre nomes das features esperadas pelo scaler.
            - Eliminação de warnings do sklearn.
            - Retorno sempre em string.
            - Tratamento completo em caso de exceções.

        Etapas internas:
            1. Obtém colunas corretas do scaler (`feature_names_in_`).
            2. Constrói DataFrame com colunas compatíveis.
            3. Chama gerar_insights_preditivos().
            4. Normaliza o resultado para formato string.
            5. Retorna fallback amigável em caso de exceção.

        Args:
            context (Dict[str, Any]):
                Informações relevantes sobre a análise atual.

        Returns:
            str:
                Insight preditivo na forma de texto simples.
        """
        try:
            # Corrige o problema do StandardScaler exigindo feature_names
            cols = getattr(scaler, "feature_names_in_", list(context.keys()))
            df_context = pd.DataFrame([context], columns=cols)

            # Chama o gerador de insights com a entrada já corrigida
            insight = gerar_insights_preditivos(model, scaler, df_context)

            # Normalização do formato de retorno
            if isinstance(insight, list):
                return insight[0] if insight else "Insight preditivo: sem retorno do modelo."
            if isinstance(insight, str):
                return insight

            return "Insight preditivo: formato inesperado retornado pelo gerador."

        except Exception:
            # Fallback simples e informativo
            if "trend" in context:
                return f"Insight preditivo (fallback): tendência atual é '{context['trend']}'."
            if "orientacao_max" in context:
                return f"Insight preditivo (fallback): orientação com maior média é {context['orientacao_max']}."
            if "corr" in context:
                return f"Insight preditivo (fallback): correlação estimada = {context['corr']:.2f}."

            return "Insight preditivo (fallback): não foi possível gerar insight do modelo."


    @staticmethod
    def gerar_pdf(response, stats: Dict[str, float], predicoes: List[Predicao]) -> None:
        """
        Método responsável por montar TODAS as páginas do PDF.

        O PDF é dividido em:
            - Capa inicial
            - Resumo estatístico
            - Gráficos 1, 2 e 3 com insights
            - Lista de insights automáticos
            - Histórico completo de predições

        Funcionamento interno:
            1. Cria um canvas no formato A4.
            2. Escreve cada seção do PDF usando métodos do ReportLab.
            3. Renderiza figuras matplotlib em memória e insere como PNG.
            4. Gera insights automáticos e preditivos.
            5. Faz paginação automática quando necessário.

        Args:
            response (HttpResponse):
                Objeto de resposta HTTP onde o PDF será escrito.
            stats (Dict[str, float]):
                Estatísticas calculadas no método GET.
            predicoes (List[Predicao]):
                Lista completa de predições ordenadas por data.
        """
        pdf = Canvas(response, pagesize=A4)
        largura, altura = A4

        # CAPA DO RELATÓRIO
        pdf.setFont("Helvetica-Bold", 28)
        pdf.drawCentredString(largura / 2, altura - 120, "Relatório de Predições")
        pdf.setFont("Helvetica", 14)
        pdf.drawCentredString(largura / 2, altura - 155, "Sistema de Eficiência Energética")

        # Nome do usuário no PDF
        usuario = predicoes[0].usuario.username if predicoes else "Usuário"
        pdf.setFont("Helvetica-Oblique", 12)
        pdf.drawCentredString(largura / 2, altura - 190, f"Gerado para: {usuario}")
        pdf.showPage()


        # RESUMO ESTATÍSTICO
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(40, altura - 60, "Resumo Estatístico")
        y = altura - 100

        # Lista cada estatística no PDF
        pdf.setFont("Helvetica", 12)
        for k, v in stats.items():
            pdf.drawString(50, y, f"- {k}: {v}")
            y -= 20
        pdf.showPage()

        # FUNÇÃO AUXILIAR PARA INSERIR GRÁFICOS
        def add_plot(fig, titulo: str, insight_text: str):
            # Salva figura em memória
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
            buf.seek(0)

            # Título do gráfico
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(40, altura - 60, titulo)

            # Insere imagem no PDF
            pdf.drawImage(ImageReader(buf), 40, altura - 420, width=520, height=300)

            # Texto do insight (quebra automática)
            pdf.setFont("Helvetica", 11)
            y_insight = altura - 440
            max_chars = 110
            lines = [insight_text[i:i + max_chars] for i in range(0, len(insight_text), max_chars)]

            for line in lines:
                pdf.drawString(40, y_insight, line)
                y_insight -= 14
            pdf.showPage()

        # PREPARA DADOS PARA GRÁFICOS
        labels = [p.data_criacao.strftime("%d/%m") for p in predicoes]
        aq_vals = [p.carga_aquecimento for p in predicoes]
        rf_vals = [p.carga_resfriamento for p in predicoes]

        # GRÁFICO 1 — EVOLUÇÃO TEMPORAL
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(labels, aq_vals, marker="o", label="Aquecimento")
        ax.plot(labels, rf_vals, marker="o", label="Resfriamento")
        ax.set_title("Evolução das Predições")
        ax.legend()

        # Insight automático: tendência simples (comparar média últimos 3 vs primeiros 3)
        def _calc_trend(vals):
            if len(vals) < 4:
                return "amostras insuficientes para tendência confiável"
            head = mean(vals[:3])
            tail = mean(vals[-3:])
            if tail > head * 1.05:
                return "tendência de alta"
            if tail < head * 0.95:
                return "tendência de queda"
            return "tendência estável"

        trend_aq = _calc_trend(aq_vals)
        trend_rf = _calc_trend(rf_vals)
        auto_insight_1 = f"Aquecimento: {trend_aq}. Resfriamento: {trend_rf}."

        # Insight preditivo
        context_1 = {
            "type": "temporal",
            "trend": {"aquecimento": trend_aq, "resfriamento": trend_rf},
            "last_values": {"aquecimento": aq_vals[-3:], "resfriamento": rf_vals[-3:]}
        }
        pred_insight_1 = PredicaoPDFView._safe_gerar_insight_preditivo(context_1)
        insight_text_1 = f"Insight preditivo: {pred_insight_1} | Observação: {auto_insight_1}"
        add_plot(fig, "Gráfico 1 — Evolução Temporal", insight_text_1)
        plt.close(fig)


        # GRÁFICO 2 — BARRAS POR ORIENTAÇÃO
        orient = {}
        for p in predicoes:
            orient.setdefault(p.orientacao, []).append(p.carga_resfriamento)

        orient_labels = list(orient.keys())
        orient_means = [mean(v) for v in orient.values()] if orient else []

        fig, ax = plt.subplots(figsize=(10, 4))
        if orient_labels:
            ax.bar(orient_labels, orient_means)
        ax.set_title("Média de Resfriamento por Orientação")

        # Insight automático: orientação com maior média
        if orient:
            max_orient = orient_labels[orient_means.index(max(orient_means))]
            auto_insight_2 = f"Orientação com maior média de resfriamento: {max_orient} (média = {max(orient_means):.2f})."
        else:
            max_orient = None
            auto_insight_2 = "Sem dados por orientação."

        # Insight preditivo (modelo) — contexto com orientação dominante
        context_2 = {
            "type": "orientacao",
            "orientacao_max": max_orient,
            "orientacao_medias": {k: mean(v) for k, v in orient.items()}
        }

        pred_insight_2 = PredicaoPDFView._safe_gerar_insight_preditivo(context_2)
        insight_text_2 = f"Insight preditivo: {pred_insight_2} | Observação: {auto_insight_2}"

        add_plot(fig, "Gráfico 2 — Barras por Orientação", insight_text_2)
        plt.close(fig)

        # GRÁFICO 3 — SCATTER ALTURA x AQUECIMENTO
        alturas = [p.altura_total for p in predicoes]
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.scatter(alturas, aq_vals)
        ax.set_title("Altura Total × Carga de Aquecimento")

        # Calcula correlação Pearson manual
        def _pearson(x, y):
            if len(x) < 2:
                return 0.0

            mx, my = mean(x), mean(y)
            num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
            den_x = (sum((xi - mx) ** 2 for xi in x)) ** 0.5
            den_y = (sum((yi - my) ** 2 for yi in y)) ** 0.5

            if den_x * den_y == 0:
                return 0.0
            return num / (den_x * den_y)

        corr = _pearson(alturas, aq_vals)
        auto_insight_3 = f"Correlação estimada (altura vs aquecimento): {corr:.2f}."

        # Insight preditivo (modelo) — contexto com correlação
        context_3 = {
            "type": "scatter",
            "corr": corr,
            "summary": {"altura_mean": mean(alturas) if alturas else None,
                        "aq_mean": mean(aq_vals) if aq_vals else None}
        }
        pred_insight_3 = PredicaoPDFView._safe_gerar_insight_preditivo(context_3)
        insight_text_3 = f"Insight preditivo: {pred_insight_3} | Observação: {auto_insight_3}"

        add_plot(fig, "Gráfico 3 — Scatter Aquecimento", insight_text_3)
        plt.close(fig)

        # INSIGHTS AUTOMÁTICOS LISTADOS
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(40, altura - 60, "Insights Automáticos")

        y = altura - 110
        pdf.setFont("Helvetica", 12)

        # Escreve cada insight um por linha
        for linha in gerar_insights_basicos(predicoes):
            pdf.drawString(50, y, f"- {linha}")
            y -= 18

            # Paginação automática
            if y < 80:
                pdf.showPage()
                y = altura - 80
        pdf.showPage()

        # HISTÓRICO COMPLETO DE PREDIÇÕES
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(40, altura - 60, "Histórico de Predições")

        pdf.setFont("Helvetica", 10)
        y = altura - 110

        for p in predicoes:
            texto = f"{p.data_criacao.strftime('%d/%m/%Y %H:%M')} — AQ: {p.carga_aquecimento} | RF: {p.carga_resfriamento}"
            pdf.drawString(40, y, texto)
            y -= 16
            if y < 60:
                pdf.showPage()
                y = altura - 80

        pdf.showPage()
        pdf.save()