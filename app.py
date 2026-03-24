import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="BIM Radar Pro 2.0", layout="wide")

# =========================
# CONFIG
# =========================
BASE_URL = "https://pncp.gov.br/api/v1/contratacoes/publicacao"

# =========================
# FUNÇÃO PRINCIPAL
# =========================
@st.cache_data(ttl=600)
def buscar_licitacoes(termo, paginas=3, valor_min=0):
    resultados = []

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    for pagina in range(0, paginas):

        params = {
            "pagina": pagina,
            "tamanhoPagina": 50,
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

            # 🔥 FILTRO LOCAL (resolve problema da API)
            for i in items:
                objeto = str(i.get('objeto', '')).lower()

                if termo.lower() not in objeto:
                    continue

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

        except Exception:
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
# UI
# =========================
st.title("🏗️ BIM Radar Pro 2.0")
st.markdown("Monitor inteligente de oportunidades do PNCP")

with st.sidebar:
    st.header("🔍 Filtros")

    termo = st.text_input("Palavra-chave", "BIM")
    paginas = st.slider("Qtd. páginas", 1, 10, 3)
    valor_min = st.number_input("Valor mínimo (R$)", 0, 10000000, 0, step=50000)

    buscar = st.button("🚀 Buscar oportunidades")

# =========================
# EXECUÇÃO
# =========================
if buscar:
    with st.spinner("Buscando oportunidades..."):
        df = buscar_licitacoes(termo, paginas, valor_min)

    if df.empty:
        st.warning("Nenhum resultado encontrado.")
        st.info("Dica: tente termos como 'obra', 'engenharia', 'projeto', 'pavimentação'")
    else:
        st.success(f"{len(df)} resultados encontrados")

        df = calcular_score(df, termo)

        # KPIs
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", len(df))
        c2.metric("Média", f"R$ {df['Valor (R$)'].mean():,.0f}")
        c3.metric("Máximo", f"R$ {df['Valor (R$)'].max():,.0f}")
        c4.metric("Top Score", df['Score'].max())

        st.markdown("---")

        # GRÁFICOS
        col1, col2 = st.columns(2)

        with col1:
            uf_count = df['UF'].value_counts().reset_index()
            uf_count.columns = ['UF', 'Quantidade']
            st.plotly_chart(px.bar(uf_count, x='UF', y='Quantidade'), use_container_width=True)

        with col2:
            st.plotly_chart(px.histogram(df, x='Valor (R$)'), use_container_width=True)

        st.markdown("---")

        # DOWNLOAD
        csv = df.to_csv(index=False).encode('utf-8')

        st.download_button(
            label="📥 Baixar CSV",
            data=csv,
            file_name=f"licitacoes_{datetime.now().date()}.csv",
            mime="text/csv"
        )

        # TABELA
        st.dataframe(
            df,
            column_config={
                "Link": st.column_config.LinkColumn("🔗 Abrir")
            },
            use_container_width=True
        )
