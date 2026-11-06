"""
Funções de dados do painel de ações da B3.

Este arquivo NÃO usa Streamlit: só recebe dados, calcula e devolve resultados.
Assim, cada função pode ser testada isoladamente (veja a pasta tests/).
"""

from io import BytesIO

import pandas as pd
import yfinance as yf

# Atenção: a EZTEC negocia como "EZTC3" (o "3" faz parte do código).
ACOES = [
    "BBSE3", "BBAS3", "BBDC4", "B3SA3", "CMIN3", "EGIE3",
    "EZTC3", "FLRY3", "GRND3", "ITSA4", "JHSF3", "KLBN11",
    "NEO3", "SAPR11", "SIMH3", "TAEE11", "TUPY3", "WEGE3",
]

DIAS_UTEIS_ANO = 252


def baixar_precos(tickers: tuple[str, ...], meses: int) -> pd.DataFrame:
    """Baixa os preços de fechamento diários das ações escolhidas.

    Retorna um DataFrame: cada linha é um dia, cada coluna é uma ação
    (sem o sufixo ".SA"). Se o download falhar, retorna um DataFrame vazio.
    """
    if not tickers:
        return pd.DataFrame()

    # O Yahoo Finance identifica ações brasileiras com o sufixo ".SA"
    tickers_yahoo = [f"{t}.SA" for t in tickers]
    inicio = pd.Timestamp.today().normalize() - pd.DateOffset(months=meses)

    dados = yf.download(
        tickers=tickers_yahoo,
        start=inicio,
        auto_adjust=True,  # ajusta os preços por dividendos e desdobramentos
        progress=False,
    )

    if dados.empty:
        return pd.DataFrame()

    precos = dados["Close"]
    # Com uma ação só, o yfinance pode devolver uma Series; viramos DataFrame
    if isinstance(precos, pd.Series):
        precos = precos.to_frame(name=tickers_yahoo[0])

    precos = precos.copy()
    precos.columns = [c.replace(".SA", "") for c in precos.columns]
    precos.index.name = "Data"
    # Remove colunas sem nenhum dado (ação sem cotação no período)
    return precos.dropna(axis=1, how="all")


def acoes_sem_dados(escolhidas: list[str], precos: pd.DataFrame) -> list[str]:
    """Lista, em ordem alfabética, as ações escolhidas que não vieram no download."""
    return sorted(set(escolhidas) - set(precos.columns))


def base_100(precos: pd.DataFrame) -> pd.DataFrame:
    """Converte os preços para base 100: cada ação começa valendo 100.

    Divide cada coluna pelo seu primeiro valor válido e multiplica por 100.
    """
    primeiro_valor = precos.bfill().iloc[0]
    return precos.div(primeiro_valor).mul(100)


def calcular_estatisticas(precos: pd.DataFrame) -> pd.DataFrame:
    """Calcula o resumo de cada ação no período (uma linha por ação)."""
    ultimo = precos.ffill().iloc[-1]
    primeiro = precos.bfill().iloc[0]
    retornos_diarios = precos.pct_change(fill_method=None)

    return pd.DataFrame({
        "Último preço (R$)": ultimo,
        "Mínimo (R$)": precos.min(),
        "Máximo (R$)": precos.max(),
        "Variação no período (%)": (ultimo / primeiro - 1) * 100,
        # Volatilidade anualizada: desvio-padrão dos retornos diários × √252
        "Volatilidade anual (%)": retornos_diarios.std() * DIAS_UTEIS_ANO ** 0.5 * 100,
    }).round(2)


def formatar_reais(valor: float) -> str:
    """Formata um número no padrão brasileiro: 1234.5 -> 'R$ 1.234,50'."""
    texto = f"{valor:,.2f}"  # padrão americano: 1,234.50
    # Troca vírgula por ponto e vice-versa, usando "X" como apoio temporário
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def gerar_excel(df: pd.DataFrame) -> bytes:
    """Converte o DataFrame em um arquivo Excel na memória (para download)."""
    buffer = BytesIO()
    df.to_excel(buffer, sheet_name="Cotações")
    return buffer.getvalue()
