"""
Testes unitários das funções de funcoes.py.

Cada teste segue o mesmo roteiro:
    1. prepara os dados de entrada
    2. chama a função
    3. confere o resultado com `assert`
"""

from io import BytesIO

import pandas as pd
import pytest
import yfinance as yf

import funcoes as f


# ---------------------------------------------------------------------------
# baixar_precos
# ---------------------------------------------------------------------------
def test_baixar_precos_retorna_uma_coluna_por_acao_sem_sufixo(yahoo_falso):
    precos = f.baixar_precos(("WEGE3", "ITSA4"), meses=6)

    assert list(precos.columns) == ["WEGE3", "ITSA4"]
    assert precos.index.name == "Data"
    assert not precos.empty


def test_baixar_precos_remove_acao_sem_cotacao(yahoo_falso):
    precos = f.baixar_precos(("WEGE3", "NEO3"), meses=6)

    assert "NEO3" not in precos.columns
    assert "WEGE3" in precos.columns


def test_baixar_precos_retorna_vazio_quando_download_falha(monkeypatch):
    monkeypatch.setattr(yf, "download", lambda *args, **kwargs: pd.DataFrame())

    assert f.baixar_precos(("WEGE3",), meses=6).empty


def test_baixar_precos_sem_acoes_nao_chama_o_yahoo(monkeypatch):
    def nao_deveria_ser_chamado(*args, **kwargs):
        raise AssertionError("yf.download não deveria ser chamado")

    monkeypatch.setattr(yf, "download", nao_deveria_ser_chamado)

    assert f.baixar_precos((), meses=6).empty


def test_baixar_precos_envia_sufixo_sa_e_data_inicial_correta(monkeypatch):
    chamada = {}

    def download_espiao(tickers, start, **kwargs):
        chamada["tickers"] = tickers
        chamada["start"] = start
        return pd.DataFrame()

    monkeypatch.setattr(yf, "download", download_espiao)
    f.baixar_precos(("WEGE3",), meses=3)

    esperado = pd.Timestamp.today().normalize() - pd.DateOffset(months=3)
    assert chamada["tickers"] == ["WEGE3.SA"]
    assert chamada["start"] == esperado


# ---------------------------------------------------------------------------
# acoes_sem_dados
# ---------------------------------------------------------------------------
def test_acoes_sem_dados_lista_as_que_faltam_em_ordem(precos_exemplo):
    faltando = f.acoes_sem_dados(["WEGE3", "NEO3", "EZTC3"], precos_exemplo)

    assert faltando == ["EZTC3", "NEO3"]


def test_acoes_sem_dados_vazio_quando_todas_vieram(precos_exemplo):
    assert f.acoes_sem_dados(["WEGE3", "ITSA4"], precos_exemplo) == []


# ---------------------------------------------------------------------------
# base_100
# ---------------------------------------------------------------------------
def test_base_100_comeca_em_100_e_mantem_proporcao(precos_exemplo):
    resultado = f.base_100(precos_exemplo)

    assert resultado.iloc[0].tolist() == [100.0, 100.0]
    assert resultado["WEGE3"].iloc[-1] == pytest.approx(150.0)
    assert resultado["ITSA4"].iloc[-1] == pytest.approx(50.0)


def test_base_100_usa_primeiro_valor_valido_quando_comeca_vazio(precos_exemplo):
    # Simula uma ação que só começou a ter cotação no segundo dia
    precos_exemplo.loc[precos_exemplo.index[0], "WEGE3"] = float("nan")

    resultado = f.base_100(precos_exemplo)

    assert resultado["WEGE3"].iloc[1] == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# calcular_estatisticas
# ---------------------------------------------------------------------------
def test_calcular_estatisticas_valores_basicos(precos_exemplo):
    est = f.calcular_estatisticas(precos_exemplo)

    assert est.loc["WEGE3", "Último preço (R$)"] == 15.0
    assert est.loc["WEGE3", "Mínimo (R$)"] == 10.0
    assert est.loc["WEGE3", "Máximo (R$)"] == 15.0
    assert est.loc["WEGE3", "Variação no período (%)"] == 50.0
    assert est.loc["ITSA4", "Variação no período (%)"] == -50.0


def test_calcular_estatisticas_volatilidade_zero_para_crescimento_constante():
    # Sobe sempre 10% ao dia -> retornos iguais -> desvio-padrão zero
    precos = pd.DataFrame({"TESTE": [100.0, 110.0, 121.0, 133.1]})

    est = f.calcular_estatisticas(precos)

    assert est.loc["TESTE", "Volatilidade anual (%)"] == pytest.approx(0.0, abs=0.01)


def test_calcular_estatisticas_tem_as_colunas_esperadas(precos_exemplo):
    est = f.calcular_estatisticas(precos_exemplo)

    assert list(est.columns) == [
        "Último preço (R$)", "Mínimo (R$)", "Máximo (R$)",
        "Variação no período (%)", "Volatilidade anual (%)",
    ]


# ---------------------------------------------------------------------------
# formatar_reais
# ---------------------------------------------------------------------------
# parametrize roda o mesmo teste várias vezes, uma para cada par (entrada, esperado)
@pytest.mark.parametrize("valor, esperado", [
    (22.5, "R$ 22,50"),
    (1234.5, "R$ 1.234,50"),
    (1234567.891, "R$ 1.234.567,89"),
    (0, "R$ 0,00"),
])
def test_formatar_reais(valor, esperado):
    assert f.formatar_reais(valor) == esperado


# ---------------------------------------------------------------------------
# gerar_excel
# ---------------------------------------------------------------------------
def test_gerar_excel_cria_arquivo_que_pode_ser_lido_de_volta(precos_exemplo):
    conteudo = f.gerar_excel(precos_exemplo)

    lido = pd.read_excel(BytesIO(conteudo), sheet_name="Cotações", index_col="Data")

    assert isinstance(conteudo, bytes)
    assert list(lido.columns) == ["WEGE3", "ITSA4"]
    assert lido["WEGE3"].tolist() == [10.0, 11.0, 12.0, 15.0]


# ---------------------------------------------------------------------------
# Lista de ações
# ---------------------------------------------------------------------------
def test_lista_de_acoes_sem_repeticao_e_sem_sufixo():
    assert len(f.ACOES) == len(set(f.ACOES))
    assert all(not a.endswith(".SA") for a in f.ACOES)
    assert "EZTC3" in f.ACOES  # o código correto da EZTEC
