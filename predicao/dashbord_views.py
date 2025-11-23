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
from predicao.services.pdf_service import PredicaoPDFService
from predicao.model_loader import model, scaler


class DashboadPredicaoView(LoginRequiredMixin, View):
    """
    View responsável por exibir o dashboard avançado contendo estatísticas,
    análises e gráficos derivados das predições realizadas pelo usuário.

    Funcionalidades:
        - Cards avançados (maior, menor, desvio padrão, etc.)
        - Gráfico de linha da evolução das predições
        - Gráfico de barras por orientação
        - Gráficos de dispersão (correlações)
        - Organização visual profissional com dados estatísticos

    Métodos:
        get(request):
            Coleta e processa os dados para renderizar o dashboard avançado.
    """

    @staticmethod
    def _safe_gerar_insight_preditivo(context: Dict[str, Any]) -> str:
        """
        Mesma função do PDF: gera insight preditivo sem warnings,
        garantindo coerência entre Dashboard e PDF.
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
        try:
            predicoes = Predicao.objects.filter(usuario=request.user).order_by("data_criacao")

            if not predicoes.exists():
                messages.info(request, "Nenhuma predição foi encontrada para gerar o dashboard.")
                return redirect("criar_predicao")

            # ----------- DADOS BÁSICOS (idêntico ao PDF) -----------------
            labels = [p.data_criacao.strftime("%d/%m") for p in predicoes]
            aq_vals = [p.carga_aquecimento for p in predicoes]
            rf_vals = [p.carga_resfriamento for p in predicoes]

            total = len(predicoes)
            maior_aq = round(max(aq_vals), 2)
            menor_resf = round(min(rf_vals), 2)
            desvio_padrao = round(stdev(aq_vals), 2) if total > 1 else 0
            mediana_geral = round(median(aq_vals + rf_vals), 2)

            # ----------- ORIENTAÇÕES (mesmo padrão do PDF) ---------
            orient = {}
            for p in predicoes:
                orient.setdefault(p.orientacao, []).append(p.carga_resfriamento)

            orient_labels = list(orient.keys())
            orient_means = [mean(v) for v in orient.values()] if orient else []

            # ----------- SCATTERS (idêntico ao PDF) -----------------
            scatter_aq = [{"x": p.altura_total, "y": p.carga_aquecimento} for p in predicoes]
            scatter_resf = [{"x": p.area_superficial, "y": p.carga_resfriamento} for p in predicoes]

            # ====================== INSIGHT 1 — Evolução Temporal ======================
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
            insight1_auto = f"Aquecimento: {trend_aq}. Resfriamento: {trend_rf}."

            context1 = {
                "type": "temporal",
                "trend": {"aquecimento": trend_aq, "resfriamento": trend_rf},
                "last_values": {"aquecimento": aq_vals[-3:], "resfriamento": rf_vals[-3:]},
            }
            insight1_pred = self._safe_gerar_insight_preditivo(context1)

            # ====================== INSIGHT 2 — Barras por Orientação ======================
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

            # ====================== INSIGHT 3 — Scatter Altura × Aquecimento ======================
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

            # ====================== INSIGHT 4 — Scatter Área × Resfriamento ======================
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


            # ===== RETURN FINAL (passamos tudo para o template) =====
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
    View responsável pelo download do PDF contendo os dados do dashboard avançado.
    """
    def get(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """
        Método GET que dispara a geração do PDF.
        """
        try:
            predicoes = Predicao.objects.filter(
                usuario=request.user
            ).order_by("data_criacao")

            if not predicoes.exists():
                messages.info(request, "Nenhuma predição disponível para gerar PDF.")
                return redirect("dashboard_predicao")

            aquecimento = [p.carga_aquecimento for p in predicoes]
            resfriamento = [p.carga_resfriamento for p in predicoes]

            stats = {
                "Total de Predições": predicoes.count(),
                "Maior Aquecimento": round(max(aquecimento), 2),
                "Menor Resfriamento": round(min(resfriamento), 2),
                "Desvio Padrão (Aquecimento)": round(stdev(aquecimento), 2) if len(aquecimento) > 1 else 0,
                "Mediana Geral": round(median(aquecimento + resfriamento), 2),
            }

            # Cria a resposta PDF
            response = HttpResponse(content_type="application/pdf")
            response["Content-Disposition"] = "attachment; filename=dashboard_predicoes.pdf"

            # Chama o método estático
            self.gerar_pdf(response, stats, predicoes)

            return response

        except Exception as e:
            report_log(request.user, "PDF Predições", "ERROR", f"Erro ao gerar PDF: {e}")
            messages.error(request, "Erro ao gerar o PDF das predições.")
            return redirect("dashboard_predicao")

    @staticmethod
    def _safe_gerar_insight_preditivo(context: Dict[str, Any]) -> str:
        """
        Gera insight preditivo usando gerar_insights_preditivos(model, scaler, context)
        sem gerar warnings do sklearn, garantindo input com nomes de colunas.
        """
        try:
            # Corrige o problema do StandardScaler exigindo feature_names
            cols = getattr(scaler, "feature_names_in_", list(context.keys()))
            df_context = pd.DataFrame([context], columns=cols)

            # Chama o gerador de insights com a entrada já corrigida
            insight = gerar_insights_preditivos(model, scaler, df_context)

            # Normaliza o retorno
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
        pdf = Canvas(response, pagesize=A4)
        largura, altura = A4

        # CAPA
        pdf.setFont("Helvetica-Bold", 28)
        pdf.drawCentredString(largura / 2, altura - 120, "Relatório de Predições")
        pdf.setFont("Helvetica", 14)
        pdf.drawCentredString(largura / 2, altura - 155, "Sistema de Eficiência Energética")
        usuario = predicoes[0].usuario.username if predicoes else "Usuário"
        pdf.setFont("Helvetica-Oblique", 12)
        pdf.drawCentredString(largura / 2, altura - 190, f"Gerado para: {usuario}")
        pdf.showPage()

        # RESUMO ESTATÍSTICO
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(40, altura - 60, "Resumo Estatístico")
        y = altura - 100
        pdf.setFont("Helvetica", 12)
        for k, v in stats.items():
            pdf.drawString(50, y, f"- {k}: {v}")
            y -= 20
        pdf.showPage()

        # Função auxiliar para adicionar figura PNG do matplotlib ao PDF
        def add_plot(fig, titulo: str, insight_text: str):
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=140, bbox_inches="tight")
            buf.seek(0)
            pdf.setFont("Helvetica-Bold", 14)
            pdf.drawString(40, altura - 60, titulo)
            pdf.drawImage(ImageReader(buf), 40, altura - 420, width=520, height=300)

            # Inserir o insight logo abaixo da figura
            pdf.setFont("Helvetica", 11)
            y_insight = altura - 440

            # se o insight for muito longo quebra em várias linhas
            max_chars = 110
            lines = [insight_text[i:i + max_chars] for i in range(0, len(insight_text), max_chars)]
            for line in lines:
                pdf.drawString(40, y_insight, line)
                y_insight -= 14
            pdf.showPage()

        # PREPARA DADOS COMUNS
        labels = [p.data_criacao.strftime("%d/%m") for p in predicoes]
        aq_vals = [p.carga_aquecimento for p in predicoes]
        rf_vals = [p.carga_resfriamento for p in predicoes]

        # ------- GRÁFICO 1: Evolução Temporal (linha) -------
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
        # Insight preditivo (modelo) — fornecemos um contexto simples
        context_1 = {
            "type": "temporal",
            "trend": {"aquecimento": trend_aq, "resfriamento": trend_rf},
            "last_values": {"aquecimento": aq_vals[-3:], "resfriamento": rf_vals[-3:]}
        }
        pred_insight_1 = PredicaoPDFView._safe_gerar_insight_preditivo(context_1)
        insight_text_1 = f"Insight preditivo: {pred_insight_1} | Observação: {auto_insight_1}"
        add_plot(fig, "Gráfico 1 — Evolução Temporal", insight_text_1)
        plt.close(fig)

        # ------- GRÁFICO 2: Barras por Orientação -------
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

        # ------- GRÁFICO 3: Scatter Altura × Aquecimento -------
        alturas = [p.altura_total for p in predicoes]
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.scatter(alturas, aq_vals)
        ax.set_title("Altura Total × Carga de Aquecimento")

        # Insight automático: cálculo de correlação simples (pearson)
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

        # INSIGHTS GERAIS (já existentes)
        pdf.setFont("Helvetica-Bold", 20)
        pdf.drawString(40, altura - 60, "Insights Automáticos")
        y = altura - 110
        pdf.setFont("Helvetica", 12)
        for linha in gerar_insights_basicos(predicoes):
            pdf.drawString(50, y, f"- {linha}")
            y -= 18
            if y < 80:
                pdf.showPage()
                y = altura - 80
        pdf.showPage()

        # HISTÓRICO
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