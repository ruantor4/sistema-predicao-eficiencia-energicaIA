
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View


from core.utils import report_log
from predicao.model_loader import model, scaler
from predicao.models import Predicao


class CriarPredicaoView(LoginRequiredMixin, View):

    def get(self, request: HttpRequest) -> HttpResponse:
        try:
            return render(request,'predicao/criar_predicao.html')

        except Exception as e:
            report_log(request.user, "Criar Predição", "ERROR", f"Erro inesperado: {e}")
            messages.error(request, "Erro ao carregar o formulário de predição.")
            return redirect('home')

    def post(self, request: HttpRequest) -> HttpResponse:
        try:
            comp = float(request.POST.get("compacidade_relativa", 0))
            area_sup = float(request.POST.get("area_superficial", 0))
            area_p = float(request.POST.get("area_parede", 0))
            area_t = float(request.POST.get("area_telhado", 0))
            altura = float(request.POST.get("altura_total", 0))
            orient = int(request.POST.get("orientacao", 0))
            area_v = float(request.POST.get("area_vidro", 0))
            dist_v = int(request.POST.get("distribuicao_area_vidro", 0))

            X = [[comp, area_sup, area_p, area_t, altura, orient, area_v, dist_v]]

            X_scaled = scaler.transform(X)

            carga_aq, carga_resf = model.predict(X_scaled)[0]

            predicao = Predicao.objects.create(
                usuario=request.user,
                compacidade_relativa=comp,
                area_superficial=area_sup,
                area_paredes=area_p,
                area_teto=area_t,
                altura_total=altura,
                orientacao=orient,
                area_vidros=area_v,
                distribuicao_vidros=dist_v,
                carga_aquecimento=carga_aq,
                carga_resfriamento=carga_resf
            )

            report_log(request.user, "Criar Predição - POST", "INFO", "Predição realizada com sucesso.")
            return render(request, "predicao/resultado_predicao.html", {
            "predicao": predicao,
            "carga_aquecimento": carga_aq,
            "carga_resfriamento": carga_resf
            })

        except Exception as e:
            report_log(request.user, "Criar Predição", "ERROR", f"Erro inesperado: {e}")
            messages.error(request, "Erro ao realizar predição.")
            return redirect('criar_predicao')


class ListarPredicoesView(LoginRequiredMixin, View):
    """
    View responsável por listar todas as predições realizadas pelo usuário logado.
    A listagem exibe as variáveis de entrada, os resultados do modelo e a data
    de realização da predição, ordenadas da mais recente para a mais antiga.

    Métodos:
        get(request):
            Consulta e apresenta o histórico de predições do usuário.
    """
    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Retorna a página contendo o histórico das predições realizadas pelo
        usuário autenticado.

        Args:
            request (HttpRequest): Requisição HTTP.

        Returns:
            HttpResponse: Página HTML contendo a tabela de predições.
        """
        try:
            predicoes = Predicao.objects.filter(
                usuario=request.user,
            ).order_by('-data_criacao')

            return render(request, "predicao/listar_predicoes.html", {
                "predicoes":predicoes
            })

        except Exception as e:
            report_log(request.user, "Listar Predições", "ERROR", f"Erro inesperado: {e}")
            messages.error(request, "Erro ao carregar o histórico de predições.")
            return redirect('home')


class ExcluirPredicaoView(LoginRequiredMixin, View):
    """
     View responsável por excluir uma predição específica, desde que ela
     pertença ao usuário autenticado. A exclusão é realizada via requisição POST,
     garantindo segurança e prevenindo remoção acidental.

     Métodos:
         post(request, pk):
             Remove a predição informada.
     """
    def post(self, request:HttpRequest, pk) -> HttpResponse:
        """
        Exclui a predição identificada pelo ID (pk), verificando se a mesma
        pertence ao usuário que está autenticado.

        Args:
        request (HttpRequest): Requisição HTTP do usuário.
        pk (int): ID da predição que será removida.

        Returns:
        HttpResponse: Redirecionamento para a listagem de predições.
        """
        try:
            pred = get_object_or_404(Predicao, pk=pk, usuario=request.user)
            pred.delete()

            report_log(request.user, "Excluir Predição", "SUCCESS", f"Predição #{pk} excluída com sucesso.")
            messages.success(request, "Predição excluída com sucesso.")
            return redirect("listar_predicoes")

        except Exception as e:
            report_log(request.user, "Excluir Predicao", "ERROR", f"Predição excluida com sucesso: {e}")
            messages.error(request,"Erro ao excluir predicao")
            return redirect("listar_predicoes")

