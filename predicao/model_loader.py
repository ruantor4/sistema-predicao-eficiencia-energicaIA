"""
Módulo responsável por carregar o modelo treinado e o scaler utilizados
nas predições de eficiência energética da AT3.

Os arquivos .pkl devem estar dentro do diretório definido em
settings.MODEL_DIR (por padrão, a pasta 'model/' na raiz do projeto).

Este módulo é importado pelas views e deve carregar:
    - best_model.pkl.pkl  → regressão final treinada na AT2
    - standard_scaler.pkl.pkl  → scaler usado no treinamento (StandardScaler/MinMax/Robust)

Caso qualquer arquivo esteja ausente ou corrompido, uma exceção clara será lançada,
facilitando o diagnóstico nos logs.
"""
from pathlib import Path
from typing import Any
import joblib
from django.conf import settings


def carregar_arquivo_pkl(path: Path) -> Any:
    """
    Carrega um arquivo .pkl do caminho informado.

    Args:
        path (Path): Caminho para o arquivo .pkl.

    Returns:
        Any: Objeto carregado, geralmente um modelo ou scaler do scikit-learn.

    Raises:
        FileNotFoundError: Caso o arquivo não seja encontrado.
        Exception: Para qualquer erro inesperado ao carregar o arquivo.
    """
    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    try:
        return joblib.load(path)
    except Exception as e:
        raise Exception(f"Erro ao carregar '{path.name}': {e}")


# Caminhos completos dos arquivos.pkl
MODEL_PATH: Path = settings.MODEL_DIR / "best_model.pkl.pkl"
SCALER_PATH: Path = settings.MODEL_DIR / "standard_scaler.pkl.pkl"


# Objetos globais carregados na importação do módulo
model: Any = carregar_arquivo_pkl(MODEL_PATH)
scaler: Any = carregar_arquivo_pkl(SCALER_PATH)
