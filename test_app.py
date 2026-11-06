"""
Testes do painel (a tela do Streamlit).

O AppTest roda o app_B3.py "por trás dos panos", sem abrir o navegador,
e permite simular cliques nos filtros e conferir o que apareceu na tela.
"""

from pathlib import Path

import pandas as pd
import pytest
import streamlit as st
import yfinance as yf
from streamlit.testing.v1 import AppTest

ARQUIVO_APP = str(Path(__file__).parent.parent / "app_B3.py")


@pytest.fixture(autouse=True)
def limpar_cache():
    """Esvazia o cache do Streamlit antes de cada teste.

    Sem isso, um teste poderia reaproveitar os dados baixados no teste anterior.
    autouse=True faz a fixture rodar sozinha em todos os testes deste arquivo.
    """
    st.cache_data.clear()


@pytest.fixture
def app(yahoo_falso):
    """Abre o painel com o Yahoo falso e roda a primeira vez."""
    return AppTest.from_file(ARQUIVO_APP, default_timeout=30).run()


def test_painel_abre_sem_erros(app):
    assert not app.exception
    assert app.title[0].value == "📈 Painel de Ações da B3"


def test_painel_mostra_um_cartao_por_acao_padrao(app):
    rotulos = [m.label for m in app.metric]
    assert rotulos == ["WEGE3", "ITSA4", "BBAS3"]


def test_painel_avisa_quando_acao_nao_tem_dados(app):
    app.sidebar.multiselect[0].set_value(["WEGE3", "NEO3"]).run()

    assert not app.exception
    assert "NEO3" in app.warning[0].value


def test_painel_pede_acao_quando_nenhuma_esta_selecionada(app):
    app.sidebar.multiselect[0].set_value([]).run()

    assert "Escolha ao menos uma ação" in app.info[0].value


def test_painel_funciona_no_modo_base_100(app):
    app.sidebar.radio[0].set_value("Rentabilidade (base 100)").run()

    assert not app.exception


def test_painel_mostra_erro_quando_download_falha(monkeypatch):
    monkeypatch.setattr(yf, "download", lambda *a, **k: pd.DataFrame())

    app = AppTest.from_file(ARQUIVO_APP, default_timeout=30).run()

    assert "Não foi possível baixar os dados" in app.error[0].value
