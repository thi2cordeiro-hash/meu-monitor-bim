import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="BIM Radar Pro", layout="wide", page_icon="🏗️")

@st.cache_data(ttl=600)
def buscar_licitacoes(termo_busca):
    # NOVA URL: Rota de consulta pública consolidada
    url = "https://pncp.gov.br/api/consulta/v1/contratacoes"
    
    # Parâmetros ajustados para a nova API
    params = {
        "pagina": 1,
        "tamanhoPagina": 50,
        "termo": termo_busca,
        "ordem": "dataPublicacao",
        "direcao": "desc"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://pncp.gov.br",
        "Referer": "https://pncp.gov.br/app/editais"
    }

    try:
        # Fazendo a requisição
        response = requests.get(url, params=params, headers=headers, timeout=20)
        
        if response.status_code == 200:
            dados = response.json()
            # A estrutura da resposta mudou: os itens agora ficam em 'data'
            items = dados.get('data', [])
            
            if not items:
                return pd.DataFrame()

            resultados = []
            for i in items:
                # Extraindo dados com segurança (usando .get para não dar erro se faltar algo)
                orgao_nome = i.get('orgaoEntidade', {}).get('razaoSocial', 'Órgão não identificado')
                uf_sigla = i.get('orgaoEntidade', {}).get('uf', 'BR')
                objeto_texto = i.get('objeto', 'Sem descrição')
                valor_est = i.get('valorEstimado', 0) or 0
                
                # Links no PNCP agora seguem este padrão estável:
                cnpj = i.get('orgaoEntidade', {}).get('cnpj', '')
                ano = i.get('anoCompra', '')
                seq = i.get('sequencialId', '')
                link_final = f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}"
                
                resultados.append({
                    "Data": i.get('dataPublicacaoPncp', '')[:10],
                    "Órgão": orgao_nome,
                    "UF": uf_sigla,
                    "Objeto": objeto_texto,
                    "Valor Estimado (R$)": float(valor_est),
                    "Link": link_final
                })
            return pd.DataFrame(resultados)
        else:
            st.error(f"O Portal do Governo (PNCP) está instável. Erro: {response.status_code}")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame()

# --- INTERFACE VISUAL ---
st.title("🏗️ BIM Radar: Monitor de Oportunidades")
st.markdown("---")

with st.sidebar:
    st.header("🔍 Filtros de Busca")
    termo = st.text_input("Termo de pesquisa:", value="BIM")
    st.info("Dica: Tente 'BIM', 'Modelagem 3D' ou 'Revit'.")
    confirmar = st.button("🚀 Pesquisar Licitações", use_container_width=True)

if confirmar:
    with st.spinner('Acessando base de dados do Governo...'):
        df = buscar_licitacoes(termo)
    
    if not df.empty:
        # Indicadores principais
        col1, col2, col3 = st.columns(3)
        col1.metric("Editais Encontrados", len(df))
        col2.metric("Ticket Médio", f"R$ {df['Valor Estimado (R$)'].mean():,.2f}")
        col3.metric("Maior Oportunidade", f"R$ {df['Valor Estimado (R$)'].max():,.2f}")

        # Gráfico de Oportunidades por Estado
        st.subheader("📍 Oportunidades por Estado (UF)")
        fig = px.bar(df['UF'].value_counts().reset_index(), x='UF', y='count', color='count', labels={'count':'Qtd'})
        st.plotly_chart(fig, use_container_width=True)

        # Tabela de Resultados
        st.subheader("📋 Lista de Editais Detalhada")
        st.dataframe(
            df, 
            column_config={
                "Link": st.column_config.LinkColumn("🔗 Abrir Edital"),
                "Valor Estimado (R$)": st.column_config.NumberColumn(format="R$ %.2f")
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Botão de Exportação para o Cliente
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Relatório para Excel", csv, f"relatorio_{termo}.csv", "text/csv")
    else:
        st.warning(f"Não encontramos licitações abertas para '{termo}' no momento. Tente outro termo.")
else:
    st.info("Bem-vindo! Digite um termo e clique em pesquisar para ver as oportunidades do mercado público.")
