import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Configuração da página para ficar larga e bonita
st.set_page_config(page_title="BIM Intelligence Hub", layout="wide", page_icon="🏗️")

# Função com CACHE (isso faz o app ficar rápido e não travar)
@st.cache_data(ttl=3600) # Guarda os dados por 1 hora
def buscar_dados(termo_busca, num_paginas):
    lista_resultados = []
    for p in range(1, num_paginas + 1):
        url = f"https://pncp.gov.br/api/pncp/v1/contratacoes?pagina={p}&tamanhoPagina=10&termo={termo_busca}"
        try:
            r = requests.get(url, timeout=10)
            dados = r.json()
            for item in dados.get('data', []):
                lista_resultados.append({
                    "Órgão": item['orgaoEntidade']['razaoSocial'],
                    "Objeto": item.get('objeto', ''),
                    "Valor (R$)": item.get('valorEstimado', 0) or 0,
                    "UF": item['orgaoEntidade'].get('uf', 'BR'),
                    "Data": item.get('dataPublicacaoPncp', '2024-01-01')[:10],
                    "Link": f"https://pncp.gov.br/app/editais/{item['orgaoEntidade']['cnpj']}/{item['anoCompra']}/{item['sequencialId']}"
                })
        except:
            continue
    return pd.DataFrame(lista_resultados)

# --- INTERFACE DO USUÁRIO ---
st.title("🏗️ BIM Intelligence Hub")
st.markdown("Monitor de Licitações em Tempo Real - Portal PNCP")

with st.sidebar:
    st.header("Configurações")
    termo = st.text_input("O que buscar?", value="BIM")
    paginas = st.slider("Quantidade de páginas", 1, 30, 10)
    so_projetos = st.checkbox("Filtrar apenas Projetos/Obras", value=True)
    btn = st.button("🔍 Atualizar Dados")

df_bruto = buscar_dados(termo, paginas)

if not df_bruto.empty:
    # Filtro de palavras-chave para remover "cursos" ou "softwares" se marcado
    if so_projetos:
        termos_projeto = ['projeto', 'executivo', 'obra', 'reforma', 'construção', 'serviços de engenharia', 'modelagem']
        df = df_bruto[df_bruto['Objeto'].str.contains('|'.join(termos_projeto), case=False)]
    else:
        df = df_bruto

    # Métricas
    c1, c2, c3 = st.columns(3)
    c1.metric("Licitações Encontradas", len(df))
    c2.metric("Valor Médio", f"R$ {df['Valor (R$)'].mean():,.2f}")
    c3.metric("Maior Valor", f"R$ {df['Valor (R$)'].max():,.2f}")

    # Gráficos
    st.subheader("📊 Análise por Estado (UF)")
    fig = px.bar(df.groupby('UF')['Valor (R$)'].sum().reset_index(), x='UF', y='Valor (R$)', color='Valor (R$)')
    st.plotly_chart(fig, use_container_width=True)

    # Tabela
    st.subheader("📋 Lista de Oportunidades")
    st.dataframe(df, column_config={"Link": st.column_config.LinkColumn("Abrir Edital")}, use_container_width=True)

    # Botão de Download
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Baixar Excel", csv, "licitacoes_bim.csv", "text/csv")
else:
    st.warning("Nenhum dado encontrado. Tente outra palavra-chave.")