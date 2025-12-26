from typing import List, Dict
import numpy as np
import pandas as pd


def gerar_insights_basicos(predicoes) -> List[str]:
    """
    Gera insights estatísticos simples a partir do histórico de predições.

    Regras:
    - Exige um número mínimo de registros para confiabilidade.
    - Utiliza correlação e desvio padrão como heurísticas.
    - Nunca lança exceção para a camada de view.

    Args:
        predicoes: QuerySet de objetos Predicao.

    Returns:
        List[str]: Lista de textos de insights automáticos.
    """
    insights = []

    if predicoes.count() < 3:
        return ["Dados insuficientes para gerar insights estatísticos confiáveis."]

    alturas = [p.altura_total for p in predicoes]
    aquec = [p.carga_aquecimento for p in predicoes]
    resf = [p.carga_resfriamento for p in predicoes]
    area_sup = [p.area_superficial for p in predicoes]

    try:
        if np.corrcoef(alturas, aquec)[0, 1] > 0.3:
            insights.append(
                "Cargas de aquecimento tendem a aumentar conforme a altura total aumenta."
            )

        if np.std(resf) > 1.5:
            insights.append(
                "As cargas de resfriamento apresentam variação acentuada nas últimas predições."
            )

        if np.corrcoef(area_sup, aquec)[0, 1] > 0.25:
            insights.append(
                "Imóveis com maior área superficial tendem a gerar maiores cargas térmicas."
            )

    except Exception:
        return ["Não foi possível calcular insights estatísticos."]

    return insights or ["O comportamento das predições está estável."]


def gerar_insights_preditivos(model, scaler, exemplo: Dict[str, float]) -> List[str]:
    """
    Gera insights preditivos simulando cenários a partir do último registro.

    Estratégia:
    - Realiza pequenas variações controladas nas variáveis de entrada.
    - Executa o pipeline real (scaler + modelo).
    - Analisa o impacto estimado nas cargas térmicas.

    Args:
        model: Modelo de Machine Learning treinado.
        scaler: Scaler utilizado no treinamento do modelo.
        exemplo (Dict[str, float]): Dados base da última predição.

    Returns:
        List[str]: Lista de insights preditivos em linguagem natural.
    """
    if not exemplo:
        return ["Ainda não há dados suficientes para gerar insights preditivos."]

    insights = []

    def predict(vars_dict: Dict[str, float]):
        """
        Executa uma predição isolada garantindo alinhamento com o scaler.
        """
        df = pd.DataFrame([vars_dict])
        df_scaled = scaler.transform(df)
        aq, resf = model.predict(df_scaled)[0]
        return aq, resf

    # Cenário 1 — aumento da altura total
    sim = exemplo.copy()
    sim["Altura_Total"] *= 1.10
    aq, _ = predict(sim)
    insights.append(
        f"Ao aumentar a altura total em 10%, a carga de aquecimento tende a ficar cerca de {aq:.2f}."
    )

    # Cenário 2 — aumento da área superficial
    sim = exemplo.copy()
    sim["Area_Superficial"] *= 1.15
    aq, _ = predict(sim)
    insights.append(
        f"Um aumento de 15% na área superficial pode elevar a carga de aquecimento para {aq:.2f}."
    )

    # Cenário 3 — teste de orientações
    orientacoes = []
    for o in range(1, 5):
        sim = exemplo.copy()
        sim["Orientacao"] = o
        _, resf = predict(sim)
        orientacoes.append((o, resf))

    melhor = min(orientacoes, key=lambda x: x[1])
    insights.append(
        f"A melhor orientação estimada para reduzir resfriamento é a orientação {melhor[0]}."
    )
    return insights