from typing import Any
from pathlib import Path

import joblib
from django.conf import settings


"""
Módulo responsável por carregar o modelo treinado e o scaler
utilizados nas predições de eficiência energética.

Os arquivos .pkl devem estar armazenados no diretório definido
em settings.MODEL_DIR (por padrão, a pasta 'model/' na raiz do projeto).
"""


# Caminhos completos dos arquivos .pkl
MODEL_PATH: Path = settings.MODEL_DIR / "modelo.pkl"    # ajuste o nome conforme o seu arquivo real
SCALER_PATH: Path = settings.MODEL_DIR / "scaler.pkl"   # idem aqui


# Objetos globais carregados na importação do módulo
model: Any = joblib.load(MODEL_PATH)
scaler: Any = joblib.load(SCALER_PATH)
