import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="BIM Radar Pro", layout="wide", page_icon="🏗️")

# Estilização para ficar com cara de software pago
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=300)
def buscar_licitacoes_premium(termo):
    # Tentaremos duas rotas diferentes para vencer o Erro 404
    rotas = [
        "https://pncp.gov.br/api/consulta/v1/contratacoes",
        "https://pncp.gov.br/api/pncp/v1/contratacoes"
    ]
    
    params = {
        "pagina": 1,
        "tamanhoPagina": 50,
        "termo": termo,
        "ordem": "dataPublicacao",
        "direcao": "desc",
        "statusId": 1
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://pncp.gov.br/app/editais",
        "Origin": "https://pncp.gov.br"
    }

    sessao = requests.Session() # Mantém a conexão estável
    
    for url in rotas:
        try:
            response = sessao.get(url, params=params, headers=headers, timeout=20)
            if response.status_code == 200:
                dados = response.json()
                # O PNCP muda a estrutura dependendo da rota, vamos tratar ambas:
                items = dados.get('data', []) if 'data' in dados else dados
                
                if not items or not isinstance(items, list):
                    continue
                
                final = []
                for i in items:
                    entidade = i.get('orgaoEntidade', {})
                    final.append({
                        "Data": i.get('dataPublicacaoPncp', '')[:10],
                        "Órgão": entidade.get('razaoSocial', 'N/A'),
                        "UF": entidade.get('uf', 'BR'),
                        "Objeto": i.get('objeto', ''),
                        "Valor (R$)": float(i.get('valorEstimado', 0) or 0),
                        "Link": f"https://pncp.gov.br/app/editais/{entidade.get('cnpj')}/{i.get('anoCompra')}/{i.get('sequencialId')}"
                    })
                return pd.DataFrame(final)
        except:
            continue
    return pd.DataFrame()

# --- INTERFACE ---
st.title("🏗️ BIM Radar: Inteligência de Mercado")

with st.sidebar:
    st.header("🔑 Área do Assinante")
    termo = st.text_input("Palavra-chave:", value="BIM")
    buscar = st.button("🚀 ATUALIZAR RADAR")
    st.divider()
    st.write("Suporte: comercial@seubimradar.com")

if buscar:
    with st.spinner('Consultando base de dados governamental...'):
        df = buscar_licitacoes_premium(termo)
    
    if not df.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Oportunidades", len(df))
        c2.metric("Valor Médio", f"R$ {df['Valor (R$)'].mean():,.2f}")
        c3.metric("Ticket Máximo", f"R$ {df['Valor (R$)'].max():,.2f}")

        st.subheader("📊 Volume por Estado")
        st.plotly_chart(px.bar(df['UF'].value_counts().reset_index(), x='UF', y='count'), use_container_width=True)

        st.subheader("📋 Lista de Editais")
        st.dataframe(df, column_config={"Link": st.column_config.LinkColumn("🔗 Abrir")}, use_container_width=True, hide_index=True)
        
        st.download_button("📥 Exportar Relatório Excel", df.to_csv(index=False).encode('utf-8-sig'), "radar_bim.csv", "text/csv")
    else:
        st.error("O sistema do governo não respondeu (Erro 404 persistente). Tente buscar por 'Engenharia' ou 'Obra' para testar a conexão.")
else:
    st.info("Digite um termo e clique em 'Atualizar Radar'.")
