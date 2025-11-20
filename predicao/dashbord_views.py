from statistics import stdev, median

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render, redirect
from django.views import View

from core.utils import report_log
from predicao.models import Predicao
from predicao.services.pdf_service import PredicaoPDFService


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
    def get(self, request:HttpRequest) -> HttpResponse:
        """
        Renderiza o dashboard com dados estatísticos e gráficos.

        Args:
            request (HttpRequest): A requisição do usuário autenticado.

        Returns:
            HttpResponse: Página HTML contendo gráficos e métricas.
        """
        try:
            # Busca predições do usuário logado
            predicoes = Predicao.objects.filter(
                usuario=request.user
            ).order_by("data_criacao")

            if not predicoes.exists():
                messages.info(request, "Nenhuma predição foi encontrada para gerar o dashboard.")
                return redirect("criar_predicao")

            # Dados para o gráfico de linha
            labels = [p.data_criacao.strftime("%d/%m") for p in predicoes]
            aquecimento = [p.carga_aquecimento for p in predicoes]
            resfriamento = [p.carga_resfriamento for p in predicoes]

            # Cards Estatísticos
            total = predicoes.count()
            maior_aq = round(max(aquecimento),2) if aquecimento else 0
            menor_resf = round(min(resfriamento), 2) if resfriamento else 0

            desvio_padrao = round(stdev(aquecimento), 2) if total > 1 else 0
            mediana_geral = round(median(aquecimento + resfriamento), 2) if (aquecimento or resfriamento) else 0

            # Gráfico de barras (média por orientação)
            orientacoes = {}

            for p in predicoes:
                orientacoes.setdefault(p.orientacao, []).append(p.carga_resfriamento)

            orientacoes_labels = list(orientacoes.keys())
            orientacoes_medias = [
                round(sum(val) / len(val), 2)
                for val in orientacoes.values()
            ]

            # Graficos de dispersão
            scatter_aq = [
                {"x": p.altura_total, "y": p.carga_aquecimento}
                for p in predicoes
            ]

            # Resfriamento x Área Total
            scatter_resf = [
                {"x": p.area_superficial, "y": p.carga_resfriamento}
                for p in predicoes
            ]

            return render(request, "predicao/dashboard.html", {
                # Dados básicos
                "labels": labels,
                "aquecimento": aquecimento,
                "resfriamento": resfriamento,

                # Cards avançados
                "total": total,
                "maior_aq": maior_aq,
                "menor_resf": menor_resf,
                "desvio_padrao": desvio_padrao,
                "mediana_geral": mediana_geral,

                # Barras por orientação
                "orientacoes_labels": orientacoes_labels,
                "orientacoes_medias": orientacoes_medias,

                # Scatter plots
                "scatter_aq": scatter_aq,
                "scatter_resf": scatter_resf,
            })

        except Exception as e:
            report_log(request.user,
                "Dashboard Predições",
                "ERROR",
                f"Erro ao carregar dashboard: {e}"
            )
            messages.error(request, "Erro ao carregar os dados do dashboard.")
            return redirect("home")

class PredicaoPDFView(View):
    """
    View responsável pelo download do PDF contendo os dados do dashboard avançado.
    """

    def get(self, request):
        try:
            predicoes = Predicao.objects.filter(usuario=request.user).order_by("data_criacao")

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

            # === Cabeçalho da resposta ===
            response = HttpResponse(content_type="application/pdf")
            response["Content-Disposition"] = "attachment; filename=dashboard_predicoes.pdf"

            PredicaoPDFService.gerar_pdf(response, stats, predicoes)

            report_log(request.user, "PDF Predições", "INFO", "PDF gerado com sucesso.")
            return response

        except Exception as e:
            report_log(request.user, "PDF Predições", "ERROR", f"Erro ao gerar PDF: {e}")
            messages.error(request, "Erro ao gerar o PDF das predições.")
            return redirect("dashboard_predicao")