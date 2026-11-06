"""
Como rodar (no terminal, dentro da pasta deste arquivo):
    pip install streamlit yfinance pandas openpyxl
    streamlit run app_B3.py
"""

from io import BytesIO

import pandas as pd
import streamlit as st
import yfinance as yf

# ---------------------------------------------------------------------------
# 1. Configuração da página
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Ações B3", page_icon="📈", layout="wide")

# ---------------------------------------------------------------------------
# 2. Lista de ações
# ---------------------------------------------------------------------------
ACOES = [
    "BBSE3", "BBAS3", "BBDC4", "B3SA3", "CMIN3", "EGIE3",
    "EZTC3", "FLRY3", "GRND3", "ITSA4", "JHSF3", "KLBN11",
    "NEO3", "SAPR11", "SIMH3", "TAEE11", "TUPY3", "WEGE3",
]


# ---------------------------------------------------------------------------
# 3. Funções de dados
# ---------------------------------------------------------------------------
# @st.cache_data guarda o resultado da função por 1 hora (ttl=3600 segundos).
# Isso evita que o Streamlit baixaria tudo de novo a cada clique no painel.
@st.cache_data(ttl=3600, show_spinner="Baixando cotações do Yahoo Finance...")
def baixar_precos(tickers: tuple[str, ...], meses: int) -> pd.DataFrame:
    """Baixa os preços de fechamento diários das ações escolhidas.

    Retorna um DataFrame: cada linha é um dia, cada coluna é uma ação.
    """
    tickers_yahoo = [f"{t}.SA" for t in tickers]
    inicio = pd.Timestamp.today().normalize() - pd.DateOffset(months=meses)

    dados = yf.download(
        tickers=tickers_yahoo,
        start=inicio,
        auto_adjust=True, 
        progress=False,
    )

    if dados.empty:
        return pd.DataFrame()

    precos = dados["Close"]
    if isinstance(precos, pd.Series):
        precos = precos.to_frame(name=tickers_yahoo[0])

    precos.columns = [c.replace(".SA", "") for c in precos.columns]
    precos.index.name = "Data"
    return precos.dropna(axis=1, how="all")


def gerar_excel(df: pd.DataFrame) -> bytes:
    """Converte o DataFrame em um arquivo Excel na memória (para download)."""
    buffer = BytesIO()
    df.to_excel(buffer, sheet_name="Cotações")
    return buffer.getvalue()

# ---------------------------------------------------------------------------
# 4. Barra lateral de filtros
# ---------------------------------------------------------------------------
st.sidebar.header("Filtros")

acoes_escolhidas = st.sidebar.multiselect(
    "Ações", options=ACOES, default=["WEGE3", "ITSA4", "BBAS3"]
)

meses = st.sidebar.slider(
    "Período (meses)", min_value=1, max_value=36, value=12
)

modo_grafico = st.sidebar.radio(
    "Mostrar o gráfico como",
    options=["Preço (R$)", "Rentabilidade (base 100)"],
    help="Base 100: todas as ações começam valendo 100 no primeiro dia, "
         "para comparar quem subiu mais, mesmo com preços muito diferentes.",
)

# ---------------------------------------------------------------------------
# 5. Corpo do painel
# ---------------------------------------------------------------------------
st.title("📈 Painel de Ações da B3")
st.caption("Fonte: Yahoo Finance (preços ajustados por proventos). "
           "Os dados podem ter alguns minutos de atraso.")

if not acoes_escolhidas:
    st.info("Escolha ao menos uma ação na barra lateral.")
    st.stop() 

precos = baixar_precos(tuple(acoes_escolhidas), meses)

if precos.empty:
    st.error("Não foi possível baixar os dados. Verifique sua conexão com a internet.")
    st.stop()

sem_dados = sorted(set(acoes_escolhidas) - set(precos.columns))
if sem_dados:
    st.warning(f"Sem cotações no período para: {', '.join(sem_dados)}. "
               "O código pode estar errado ou a ação pode ter saído da bolsa.")

# --- 5.1 Cartões com último preço e variação no período ---------------------
st.subheader("Resumo do período")

# Até 6 cartões por linha
colunas = st.columns(min(len(precos.columns), 6))
for i, acao in enumerate(precos.columns):
    serie = precos[acao].dropna()
    ultimo = serie.iloc[-1]
    variacao = (ultimo / serie.iloc[0] - 1) * 100
    colunas[i % len(colunas)].metric(
        label=acao,
        value=f"R$ {ultimo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        delta=f"{variacao:+.1f}%",
    )

# --- 5.2 Gráfico -------------------------------------------------------------
st.subheader("Evolução")

if modo_grafico == "Preço (R$)":
    dados_grafico = precos
    eixo_y = "Preço (R$)"
else:
    dados_grafico = precos.div(precos.bfill().iloc[0]).mul(100)
    eixo_y = "Base 100"

st.line_chart(dados_grafico, y_label=eixo_y, x_label="Data")

# --- 5.3 Tabela de estatísticas ---------------------------------------------
st.subheader("Estatísticas")

retornos_diarios = precos.pct_change()
estatisticas = pd.DataFrame({
    "Último preço (R$)": precos.ffill().iloc[-1],
    "Mínimo (R$)": precos.min(),
    "Máximo (R$)": precos.max(),
    "Variação no período (%)": (precos.ffill().iloc[-1] / precos.bfill().iloc[0] - 1) * 100,
    # Volatilidade anualizada: desvio-padrão dos retornos diários × √252 (dias úteis no ano)
    "Volatilidade anual (%)": retornos_diarios.std() * (252 ** 0.5) * 100,
}).round(2)

st.dataframe(estatisticas, width="stretch")

# --- 5.4 Dados brutos e download --------------------------------------------
with st.expander("Ver cotações diárias"):
    st.dataframe(precos.sort_index(ascending=False).round(2), width="stretch")

st.download_button(
    label="⬇️ Baixar cotações em Excel",
    data=gerar_excel(precos.round(2)),
    file_name="cotacoes_B3.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
