import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="BIM Intelligence Hub", layout="wide", page_icon="🏗️")

# Função de busca corrigida
@st.cache_data(ttl=600) # Guarda por 10 minutos para testes rápidos
def buscar_dados(termo_busca, num_paginas):
    lista_resultados = []
    
    # Cabeçalho para evitar bloqueio do portal do governo
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    for p in range(1, num_paginas + 1):
        # URL oficial de consulta do PNCP
        url = f"https://pncp.gov.br/api/pncp/v1/contratacoes"
        
        params = {
            "pagina": p,
            "tamanhoPagina": 10,
            "termo": termo_busca,
            "statusId": 1 # Apenas licitações em andamento/abertas
        }

        try:
            r = requests.get(url, params=params, headers=headers, timeout=15)
            if r.status_code == 200:
                dados = r.json()
                items = dados.get('data', [])
                
                for item in items:
                    objeto = item.get('objeto', '')
                    orgao = item.get('orgaoEntidade', {}).get('razaoSocial', 'Não informado')
                    uf = item.get('orgaoEntidade', {}).get('uf', 'BR')
                    valor = item.get('valorEstimado', 0)
                    
                    # Montagem do Link
                    cnpj = item.get('orgaoEntidade', {}).get('cnpj', '')
                    ano = item.get('anoCompra', '')
                    seq = item.get('sequencialId', '')
                    link = f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}"
                    
                    lista_resultados.append({
                        "Órgão": orgao,
                        "Objeto": objeto,
                        "Valor (R$)": valor if valor else 0,
                        "UF": uf,
                        "Data": item.get('dataPublicacaoPncp', '')[:10],
                        "Link": link
                    })
            else:
                st.error(f"Erro na conexão com o Governo (Código {r.status_code})")
        except Exception as e:
            st.error(f"Erro inesperado: {e}")
            continue
            
    return pd.DataFrame(lista_resultados)

# --- INTERFACE ---
st.title("🏗️ BIM Intelligence Hub")
st.markdown("Busca Profissional de Licitações - Portal Nacional (PNCP)")

with st.sidebar:
    st.header("🔍 Filtros de Venda")
    termo = st.text_input("Palavra-chave:", value="BIM")
    paginas = st.number_input("Páginas de busca:", min_value=1, max_value=50, value=5)
    so_projetos = st.checkbox("Filtrar Projetos (Remover cursos/softwares)", value=False)
    st.divider()
    btn = st.button("🚀 Buscar Oportunidades", use_container_width=True)

if btn:
    df = buscar_dados(termo, paginas)

    if not df.empty:
        # Filtro opcional de Projetos
        if so_projetos:
            palavras_projeto = ['projeto', 'executivo', 'obra', 'reforma', 'construção', 'engenharia', 'modelagem']
            df = df[df['Objeto'].str.contains('|'.join(palavras_projeto), case=False, na=False)]

        # Métricas
        c1, c2, c3 = st.columns(3)
        c1.metric("Resultados", len(df))
        c2.metric("Valor Médio", f"R$ {df['Valor (R$)'].mean():,.2f}")
        c3.metric("Ticket Máximo", f"R$ {df['Valor (R$)'].max():,.2f}")

        # Gráfico por Estado
        st.subheader("📍 Onde estão as oportunidades?")
        contagem_uf = df['UF'].value_counts().reset_index()
        contagem_uf.columns = ['UF', 'Quantidade']
        fig = px.bar(contagem_uf, x='UF', y='Quantidade', color='Quantidade', title="Número de Editais por Estado")
        st.plotly_chart(fig, use_container_width=True)

        # Tabela Final
        st.subheader("📋 Editais Encontrados")
        st.dataframe(
            df, 
            column_config={"Link": st.column_config.LinkColumn("Ver Edital")},
            use_container_width=True,
            hide_index=True
        )
        
        # Botão para baixar
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Exportar para Excel/CSV", csv, "oportunidades_bim.csv", "text/csv")
    else:
        st.warning(f"O portal PNCP não retornou nada para '{termo}'. Tente termos mais amplos como 'Obras' ou 'Projeto'.")
else:
    st.info("Ajuste os termos ao lado e clique no botão para iniciar a busca.")
