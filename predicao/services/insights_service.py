from typing import List, Dict
import numpy as np


def gerar_insights_basicos(predicoes) -> List[str]:
    """
    Gera insights simples baseados nos dados históricos salvos pelo usuário.
    """

    insights = []

    if not predicoes.exists():
        return ["Nenhuma predição foi realizada ainda para gerar insights."]

    alturas = [p.altura_total for p in predicoes]
    aquec = [p.carga_aquecimento for p in predicoes]
    resf = [p.carga_resfriamento for p in predicoes]
    area_sup = [p.area_superficial for p in predicoes]

    # Insight 1 – altura influencia aquecimento
    if np.corrcoef(alturas, aquec)[0][1] > 0.3:
        insights.append("Cargas de aquecimento tendem a aumentar conforme a altura total aumenta.")

    # Insight 2 – resfriamento instável
    if np.std(resf) > 1.5:
        insights.append("As cargas de resfriamento apresentam variação acentuada nas últimas predições.")

    # Insight 3 – área superficial influencia cargas
    if np.corrcoef(area_sup, aquec)[0][1] > 0.25:
        insights.append("Imóveis com maior área superficial tendem a gerar maiores cargas térmicas.")

    if not insights:
        insights.append("O comportamento das predições está estável e sem tendências marcantes.")

    return insights


def gerar_insights_preditivos(model, scaler, exemplo: Dict[str, float]) -> List[str]:
    """
    Gera insights preditivos usando o modelo real (cenários simulados).
    """

    if not exemplo:
        return ["Ainda não há dados suficientes para gerar insights preditivos."]

    insights = []

    def predict(vars_dict):
        arr = np.array([[vars_dict[k] for k in vars_dict]])
        arr_scaled = scaler.transform(arr)
        aq, resf = model.predict(arr_scaled)[0]
        return aq, resf

    # Cenário 1 – +10% na altura
    sim = exemplo.copy()
    sim["altura_total"] *= 1.10
    aq, _ = predict(sim)
    insights.append(f"Ao aumentar a altura total em 10%, a carga de aquecimento tende a ficar cerca de {aq:.2f}.")

    # Cenário 2 – +15% na área superficial
    sim = exemplo.copy()
    sim["area_superficial"] *= 1.15
    aq, _ = predict(sim)
    insights.append(f"Um aumento de 15% na área superficial pode elevar a carga de aquecimento para {aq:.2f}.")

    # Cenário 3 – melhor orientação
    orientacoes = []
    for o in range(1, 5):
        sim = exemplo.copy()
        sim["orientacao"] = o
        _, resf = predict(sim)
        orientacoes.append((o, resf))

    melhor = sorted(orientacoes, key=lambda x: x[1])[0]
    insights.append(f"A melhor orientação estimada para reduzir resfriamento é a orientação {melhor[0]}.")

    return insights
