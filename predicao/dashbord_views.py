from statistics import mean, median, stdev
from typing import List

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.views import View

from core.utils import report_log
from predicao.models import Predicao
from predicao.model_loader import model, scaler
from predicao.services.insights_service import (
    gerar_insights_basicos,
    gerar_insights_preditivos,
)
from predicao.services.pdf_service import PredicaoPDFService


class DashboadPredicaoView(LoginRequiredMixin, View):
    """
    View responsável por exibir o dashboard de predições do usuário autenticado.

    Funções principais:
    - Buscar o histórico de predições do usuário.
    - Calcular métricas estatísticas básicas.
    - Preparar dados para gráficos (linha, barras e dispersão).
    - Gerar insights automáticos e preditivos.
    - Renderizar o template do dashboard.
    """

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Processa a requisição GET do dashboard.

        Fluxo:
        - Busca predições do usuário.
        - Calcula estatísticas e estruturas de gráficos.
        - Gera insights estatísticos e preditivos.
        - Renderiza o dashboard.

        Returns:
            HttpResponse: Página HTML do dashboard.
        """
        try:
            predicoes = Predicao.objects.filter(
                usuario=request.user
            ).order_by("data_criacao")

            if not predicoes.exists():
                messages.info(
                    request,
                    "Nenhuma predição foi encontrada para gerar o dashboard."
                )
                return redirect("criar_predicao")


            # DADOS BÁSICOS

            labels = [p.data_criacao.strftime("%d/%m") for p in predicoes]
            aquecimento = [p.carga_aquecimento for p in predicoes]
            resfriamento = [p.carga_resfriamento for p in predicoes]

            total = predicoes.count()
            maior_aq = round(max(aquecimento), 2)
            menor_resf = round(min(resfriamento), 2)
            desvio_padrao = round(stdev(aquecimento), 2) if total > 1 else 0
            mediana_geral = round(median(aquecimento + resfriamento), 2)


            # ORIENTAÇÃO

            orient = {}
            for p in predicoes:
                orient.setdefault(p.orientacao, []).append(p.carga_resfriamento)

            orientacoes_labels = list(orient.keys())
            orientacoes_medias = [mean(v) for v in orient.values()] if orient else []

            # SCATTER

            scatter_aq = [{"x": p.altura_total, "y": p.carga_aquecimento} for p in predicoes]
            scatter_resf = [{"x": p.area_superficial, "y": p.carga_resfriamento} for p in predicoes]

            # INSIGHTS

            insights_basicos = gerar_insights_basicos(predicoes)

            ultima = predicoes.last()
            exemplo = {
                "Compacidade_Relativa": ultima.compacidade_relativa,
                "Area_Superficial": ultima.area_superficial,
                "Area_Parede": ultima.area_paredes,
                "Area_Telhado": ultima.area_teto,
                "Altura_Total": ultima.altura_total,
                "Orientacao": ultima.orientacao,
                "Area_Vidro": ultima.area_vidros,
                "Distribuicao_Area_Vidro": ultima.distribuicao_vidros,
            }

            insights_preditivos = gerar_insights_preditivos(
                model,
                scaler,
                exemplo
            )

            # RENDER

            return render(
                request,
                "predicao/dashboard.html",
                {
                    "labels": labels,
                    "aquecimento": aquecimento,
                    "resfriamento": resfriamento,

                    "total": total,
                    "maior_aq": maior_aq,
                    "menor_resf": menor_resf,
                    "desvio_padrao": desvio_padrao,
                    "mediana_geral": mediana_geral,

                    "orientacoes_labels": orientacoes_labels,
                    "orientacoes_medias": orientacoes_medias,

                    "scatter_aq": scatter_aq,
                    "scatter_resf": scatter_resf,

                    "insights_basicos": insights_basicos,
                    "insights_preditivos": insights_preditivos,
                }
            )

        except Exception as e:
            report_log(
                request.user,
                "Dashboard Predições",
                "ERROR",
                str(e)
            )
            messages.error(request, "Erro ao carregar o dashboard.")
            return redirect("home")


class PredicaoPDFView(View):
    """
    View responsável por gerar o PDF do dashboard de predições.

    - Busca dados do usuário autenticado.
    - Calcula estatísticas básicas.
    - Delegada a geração do PDF ao PredicaoPDFService.
    """

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Gera e retorna o PDF do dashboard.

        Returns:
            HttpResponse: Arquivo PDF para download.
        """
        try:
            predicoes = Predicao.objects.filter(
                usuario=request.user
            ).order_by("data_criacao")

            if not predicoes.exists():
                messages.info(
                    request,
                    "Nenhuma predição disponível para gerar PDF."
                )
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

            response = HttpResponse(content_type="application/pdf")
            response["Content-Disposition"] = "attachment; filename=dashboard_predicoes.pdf"

            PredicaoPDFService.gerar_pdf(
                response=response,
                stats=stats,
                registros=list(predicoes)
            )

            return response

        except Exception as e:
            report_log(
                request.user,
                "Gerar PDF Predições",
                "ERROR",
                str(e)
            )
            messages.error(request, "Erro ao gerar o PDF.")
            return redirect("dashboard_predicao")