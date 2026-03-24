import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# Configuração visual
st.set_page_config(page_title="BIM Radar", layout="wide", page_icon="🏗️")

@st.cache_data(ttl=3600)
def buscar_licitacoes(termo_busca):
    # URL da API de Contratações (Versão mais estável)
    url = "https://pncp.gov.br/api/pncp/v1/contratacoes"
    
    # Parâmetros que o governo exige
    params = {
        "pagina": 1,
        "tamanhoPagina": 20,
        "termo": termo_busca,
        "statusId": 1  # 1 = Em andamento
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*"
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
                resultados.append({
                    "Órgão": i['orgaoEntidade']['razaoSocial'],
                    "Objeto": i.get('objeto', ''),
                    "Valor (R$)": i.get('valorEstimado', 0) or 0,
                    "UF": i['orgaoEntidade'].get('uf', 'BR'),
                    "Data": i.get('dataPublicacaoPncp', '')[:10],
                    "Link": f"https://pncp.gov.br/app/editais/{i['orgaoEntidade']['cnpj']}/{i['anoCompra']}/{i['sequencialId']}"
                })
            return pd.DataFrame(resultados)
        else:
            st.error(f"O servidor do Governo respondeu com erro {response.status_code}. Tente novamente em instantes.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return pd.DataFrame()

# --- INTERFACE ---
st.title("🏗️ BIM Radar: Monitor de Licitações")

with st.sidebar:
    st.header("Busca")
    termo = st.text_input("Palavra-chave:", value="BIM")
    confirmar = st.button("🔍 Buscar Agora")

if confirmar:
    df = buscar_licitacoes(termo)
    
    if not df.empty:
        # Métricas
        c1, c2 = st.columns(2)
        c1.metric("Editais Ativos", len(df))
        c2.metric("Ticket Médio", f"R$ {df['Valor (R$)'].mean():,.2f}")

        # Gráfico Simples
        st.subheader("Oportunidades por Estado")
        st.bar_chart(df['UF'].value_counts())

        # Tabela
        st.subheader("Resultados")
        st.dataframe(
            df, 
            column_config={"Link": st.column_config.LinkColumn("Abrir")},
            use_container_width=True
        )
    else:
        st.warning(f"Nenhum edital aberto encontrado para '{termo}' hoje.")
else:
    st.info("Digite um termo (ex: BIM, Projeto, Engenharia) e clique no botão.")
