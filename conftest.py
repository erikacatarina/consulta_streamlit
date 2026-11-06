"""
Configurações compartilhadas pelos testes.

O pytest lê este arquivo automaticamente. As "fixtures" definidas aqui
podem ser usadas em qualquer teste, bastando colocar o nome delas como
parâmetro da função de teste.
"""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def precos_exemplo() -> pd.DataFrame:
    """Preços simples e conhecidos, para conferir os cálculos de cabeça."""
    datas = pd.to_datetime(["2026-01-02", "2026-01-05", "2026-01-06", "2026-01-07"])
    return pd.DataFrame(
        {
            "WEGE3": [10.0, 11.0, 12.0, 15.0],   # subiu 50%
            "ITSA4": [20.0, 18.0, 16.0, 10.0],   # caiu 50%
        },
        index=pd.Index(datas, name="Data"),
    )


def criar_download_falso(sem_dados=()):
    """Cria uma função que imita o yf.download, sem acessar a internet.

    Os tickers em `sem_dados` voltam só com NaN (como uma ação sem cotação).
    """
    def download_falso(tickers, start, **kwargs):
        datas = pd.bdate_range(start, periods=30)
        rng = np.random.default_rng(42)
        colunas = {}
        for t in tickers:
            if t in sem_dados:
                colunas[t] = np.nan
            else:
                colunas[t] = 30 * np.exp(np.cumsum(rng.normal(0, 0.01, len(datas))))
        fechamento = pd.DataFrame(colunas, index=datas)
        # O yfinance devolve colunas em dois níveis: ("Close", "WEGE3.SA")
        return pd.concat({"Close": fechamento}, axis=1)

    return download_falso


@pytest.fixture
def yahoo_falso(monkeypatch):
    """Troca o yf.download pelo download falso durante o teste."""
    import yfinance as yf

    monkeypatch.setattr(yf, "download", criar_download_falso(sem_dados={"NEO3.SA"}))
