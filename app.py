"""
BIM Radar Pro 2.0
Versão robusta com fallback automático para ambientes SEM Streamlit.

Como usar:
1) Com Streamlit (recomendado):
   pip install streamlit pandas requests plotly
   streamlit run app.py

2) Sem Streamlit (modo debug / servidor simples):
   python app.py
"""

import pandas as pd
import requests
from datetime import datetime

# =========================
# TENTATIVA DE IMPORT STREAMLIT
# =========================
try:
    import streamlit as st
    import plotly.express as px
    STREAMLIT_AVAILABLE = True
except ModuleNotFoundError:
    STREAMLIT_AVAILABLE = False

# =========================
# CONFIG
# =========================
BASE_URL = "https://pncp.gov.br/api/v1/contratacoes/publicacao"

# =========================
# FUNÇÃO PRINCIPAL
# =========================
def buscar_licitacoes(termo, paginas=3, valor_min=0):
    resultados = []

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    for pagina in range(1, paginas + 1):
        params = {
            "pagina": pagina,
            "tamanhoPagina": 50,
            "termo": termo,
            "ordenacao": "dataPublicacao",
            "direcao": "DESC"
        }

        try:
            response = requests.get(BASE_URL, params=params, headers=headers, timeout=20)

            if response.status_code != 200:
                continue

            dados = response.json()

            items = (
                dados.get("data") or
                dados.get("items") or
                dados.get("content") or
                []
            )

            for i in items:
                valor = float(i.get('valorEstimado') or 0)

                if valor < valor_min:
                    continue

                entidade = i.get('orgaoEntidade') or {}

                resultados.append({
                    "Data": str(i.get('dataPublicacao'))[:10],
                    "Órgão": entidade.get('razaoSocial', 'N/A'),
                    "UF": entidade.get('uf', 'BR'),
                    "Objeto": i.get('objeto', ''),
                    "Valor (R$)": valor,
                    "Link": f"https://pncp.gov.br/app/editais/{entidade.get('cnpj')}/{i.get('anoCompra')}/{i.get('sequencialCompra')}"
                })

        except Exception as e:
            print(f"Erro na página {pagina}: {e}")
            continue

    return pd.DataFrame(resultados)

# =========================
# SCORE
# =========================
def calcular_score(df, termo):
    scores = []

    for _, row in df.iterrows():
        score = 0

        if row['Valor (R$)'] > 1_000_000:
            score += 3
        elif row['Valor (R$)'] > 300_000:
            score += 2
        else:
            score += 1

        if termo.lower() in str(row['Objeto']).lower():
            score += 2

        scores.append(score)

    df['Score'] = scores
    return df.sort_values(by='Score', ascending=False)

# =========================
# MODO STREAMLIT
# =========================
if STREAMLIT_AVAILABLE:
    st.set_page_config(page_title="BIM Radar Pro 2.0", layout="wide")

    st.title("🏗️ BIM Radar Pro 2.0")
    st.markdown("Monitor inteligente de oportunidades do PNCP")

    with st.sidebar:
        st.header("🔍 Filtros")

        termo = st.text_input("Palavra-chave", "BIM")
        paginas = st.slider("Qtd. páginas", 1, 10, 3)
        valor_min = st.number_input("Valor mínimo (R$)", 0, 10000000, 0, step=50000)

        buscar = st.button("🚀 Buscar oportunidades")

    if buscar:
        with st.spinner("Buscando..."):
            df = buscar_licitacoes(termo, paginas, valor_min)

        if df.empty:
            st.warning("Nenhum resultado encontrado.")
        else:
            df = calcular_score(df, termo)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total", len(df))
            c2.metric("Média", f"R$ {df['Valor (R$)'].mean():,.0f}")
            c3.metric("Máximo", f"R$ {df['Valor (R$)'].max():,.0f}")
            c4.metric("Score", df['Score'].max())

            uf_count = df['UF'].value_counts().reset_index()
            uf_count.columns = ['UF', 'Quantidade']

            st.plotly_chart(px.bar(uf_count, x='UF', y='Quantidade'), use_container_width=True)
            st.plotly_chart(px.histogram(df, x='Valor (R$)'), use_container_width=True)

            csv = df.to_csv(index=False).encode('utf-8')

            st.download_button("📥 Baixar CSV", csv, f"licitacoes_{datetime.now().date()}.csv")

            st.dataframe(df, use_container_width=True)

# =========================
# MODO TERMINAL (DEBUG)
# =========================
else:
    print("⚠️ Streamlit não instalado. Rodando modo terminal...\n")

    termo = "BIM"
    df = buscar_licitacoes(termo, paginas=2)

    if df.empty:
        print("Nenhum resultado encontrado.")
    else:
        df = calcular_score(df, termo)
        print(df.head(10))

# =========================
# TESTES BÁSICOS
# =========================
def _test_busca():
    df = buscar_licitacoes("BIM", paginas=1)
    assert isinstance(df, pd.DataFrame)


def _test_score():
    df = pd.DataFrame([
        {"Objeto": "Projeto BIM", "Valor (R$)": 1000000},
        {"Objeto": "Outro", "Valor (R$)": 10000}
    ])
    df = calcular_score(df, "BIM")
    assert "Score" in df.columns


if __name__ == "__main__":
    _test_busca()
    _test_score()
    print("\n✅ Testes básicos passaram.")
