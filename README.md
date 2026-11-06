# 📈 Painel de Ações da B3

Painel interativo em Python e Streamlit para acompanhar ações da B3. Baixa cotações do Yahoo Finance (yfinance) e permite filtrar ações e período, comparar rentabilidade em base 100, ver preço atual, variação, mínimo, máximo e volatilidade, além de exportar os dados para Excel.

![Painel](docs/painel.png)

## Funcionalidades

- **Filtros:** escolha uma ou mais ações e um período de 1 a 36 meses.
- **Resumo:** cartões com o último preço e a variação no período.
- **Gráfico:** evolução do preço em R$ ou da rentabilidade em **base 100**, em que todas as ações partem de 100 para facilitar a comparação.
- **Estatísticas:** último preço, mínimo, máximo, variação (%) e volatilidade anualizada (%).
- **Exportação:** download das cotações diárias em Excel.
- **Avisos:** o painel informa quando uma ação não tem cotação no período ou quando o download falha.

Ações disponíveis: BBSE3, BBAS3, BBDC4, B3SA3, CMIN3, EGIE3, EZTC3, FLRY3, GRND3, ITSA4, JHSF3, KLBN11, NEO3, SAPR11, SIMH3, TAEE11, TUPY3 e WEGE3. Para mudar a lista, edite `ACOES` em `funcoes.py`.

## Como rodar

```bash
pip install -r requirements.txt
streamlit run app_B3.py
```

O painel abre no navegador em `http://localhost:8501`.

## Estrutura do projeto

```
├── app_B3.py            # interface do painel (Streamlit)
├── funcoes.py           # funções de dados e cálculos (sem Streamlit)
├── requirements.txt     # bibliotecas necessárias
├── pytest.ini           # configuração dos testes
├── docs/painel.png      # imagem do painel
└── tests/
    ├── conftest.py      # dados de exemplo e Yahoo Finance simulado
    ├── test_funcoes.py  # testes unitários das funções
    └── test_app.py      # testes da interface
```

A interface (`app_B3.py`) e os cálculos (`funcoes.py`) ficam separados para que as funções possam ser testadas sem abrir o painel.

## Testes

```bash
pytest -v
```

Os testes **não acessam a internet**. O `yf.download` é substituído por uma versão simulada (via `monkeypatch`), o que deixa os resultados rápidos e sempre iguais.

### Cenários testados

| Função / parte | Cenários |
|---|---|
| `baixar_precos` | retorna uma coluna por ação, sem o sufixo `.SA`; remove ações sem cotação; retorna vazio se o download falhar; não chama o Yahoo se nenhuma ação for passada; envia os tickers com `.SA` e a data inicial correta |
| `acoes_sem_dados` | lista as ações que faltaram, em ordem alfabética; retorna lista vazia quando todas vieram |
| `base_100` | começa em 100 e mantém a proporção (+50% → 150); usa o primeiro valor válido quando a série começa vazia |
| `calcular_estatisticas` | último preço, mínimo, máximo e variação corretos; volatilidade zero para crescimento constante; colunas esperadas |
| `formatar_reais` | formato brasileiro (`R$ 1.234,50`), incluindo milhões e zero |
| `gerar_excel` | gera um arquivo Excel que pode ser lido de volta com os mesmos dados |
| `ACOES` | sem repetições, sem sufixo `.SA`, com o código correto da EZTEC (`EZTC3`) |
| Painel (`app_B3.py`) | abre sem erros; mostra um cartão por ação; avisa sobre ação sem dados; pede uma ação quando nenhuma está selecionada; funciona no modo base 100; mostra erro quando o download falha |

## Observações

- Os preços são **ajustados por proventos** (dividendos e desdobramentos), por isso podem diferir do preço "de tela" do passado.
- Os dados do Yahoo Finance podem ter atraso e não devem ser usados como recomendação de investimento.

## Tecnologias

Python · Streamlit · pandas · yfinance · openpyxl · pytest
