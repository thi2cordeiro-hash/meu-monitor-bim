import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="BIM Radar Pro", layout="wide", page_icon="🏗️")

@st.cache_data(ttl=600)
def buscar_licitacoes(termo_busca):
    # ROTA DE CONSULTA PÚBLICA (A mais estável do PNCP)
    url = "https://pncp.gov.br/api/consulta/v1/contratacoes"
    
    # Parâmetros que o portal espera na busca
    params = {
        "pagina": 1,
        "tamanhoPagina": 50,
        "termo": termo_busca,
        "ordem": "dataPublicacao",
        "direcao": "desc"
    }
    
    # Cabeçalhos "Humanos" para evitar o Erro 404/403
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://pncp.gov.br",
        "Referer": "https://pncp.gov.br/app/editais"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=20)
        
        if response.status_code == 200:
            dados = response.json()
            items = dados.get('data', [])
            
            if not items:
                return pd.DataFrame()

            resultados = []
            for i in items:
                # Extração segura de dados
                orgao = i.get('orgaoEntidade', {}).get('razaoSocial', 'Órgão não identificado')
                uf = i.get('orgaoEntidade', {}).get('uf', 'BR')
                objeto = i.get('objeto', 'Sem descrição')
                valor = i.get('valorEstimado', 0) or 0
                
                # Montagem do link padrão PNCP
                cnpj = i.get('orgaoEntidade', {}).get('cnpj', '')
                ano = i.get('anoCompra', '')
                seq = i.get('sequencialId', '')
                link = f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{seq}"
                
                resultados.append({
                    "Data": i.get('dataPublicacaoPncp', '')[:10],
                    "Órgão": orgao,
                    "UF": uf,
                    "Objeto": objeto,
                    "Valor Estimado (R$)": float(valor),
                    "Link": link
                })
            return pd.DataFrame(resultados)
        else:
            # Se der erro, mostramos o código para diagnóstico
            st.error(f"Erro de comunicação com o PNCP (Código {response.status_code}).")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame()

# --- INTERFACE ---
st.title("🏗️ BIM Radar: Monitor de Oportunidades")
st.markdown("Busca em tempo real no Portal Nacional de Contratações Públicas.")

with st.sidebar:
    st.header("🔍 Filtros")
    termo = st.text_input("Termo de pesquisa:", value="BIM")
    confirmar = st.button("🚀 Pesquisar Agora", use_container_width=True)

if confirmar:
    with st.spinner('Conectando ao servidor do Governo...'):
        df = buscar_licitacoes(termo)
    
    if not df.empty:
        # Métricas no topo
        c1, c2, c3 = st.columns(3)
        c1.metric("Editais Ativos", len(df))
        c2.metric("Ticket Médio", f"R$ {df['Valor Estimado (R$)'].mean():,.2f}")
        c3.metric("Maior Valor", f"R$ {df['Valor Estimado (R$)'].max():,.2f}")

        # Gráfico por Estado
        st.subheader("📍 Oportunidades por Estado")
        fig = px.bar(df['UF'].value_counts().reset_index(), x='UF', y='count', color='count')
        st.plotly_chart(fig, use_container_width=True)

        # Tabela interativa
        st.subheader("📋 Lista de Editais")
        st.dataframe(
            df, 
            column_config={
                "Link": st.column_config.LinkColumn("🔗 Abrir Edital"),
                "Valor Estimado (R$)": st.column_config.NumberColumn(format="R$ %.2f")
            },
            use_container_width=True,
            hide_index=True
        )
        
        # Exportação
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Relatório (Excel/CSV)", csv, f"licitacoes_{termo}.csv", "text/csv")
    else:
        st.warning(f"Nenhum edital encontrado para '{termo}'. Tente termos como 'Projeto' ou 'Engenharia'.")
else:
    st.info("Digite um termo e clique em pesquisar.")
