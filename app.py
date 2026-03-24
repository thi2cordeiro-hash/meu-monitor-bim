import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# 1. Título e Configuração da sua Marca
st.set_page_config(page_title="BIM Radar Pro", layout="wide", page_icon="🏗️")

st.title("🏗️ BIM Radar: Inteligência de Mercado")
st.subheader("Plataforma Profissional de Monitoramento PNCP")

# 2. Função de Busca (Ajustada para evitar erro 404)
@st.cache_data(ttl=600)
def buscar_licitacoes_seguro(termo_busca):
    # Rota mais estável detectada em 2026
    url = "https://pncp.gov.br/api/pncp/v1/contratacoes"
    
    # Parâmetros simplificados para garantir resposta
    params = {
        "pagina": 1,
        "tamanhoPagina": 50,
        "termo": termo_busca,
        "statusId": 1  # 1 significa 'Em andamento/Aberto'
    }
    
    # Cabeçalhos que simulam um computador real (evita bloqueios)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://pncp.gov.br/app/editais",
        "Origin": "https://pncp.gov.br"
    }

    try:
        # Tentativa de conexão
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            dados = response.json()
            items = dados.get('data', [])
            
            if not items:
                return pd.DataFrame()

            lista = []
            for i in items:
                # Pegando as informações com cuidado
                entidade = i.get('orgaoEntidade', {})
                lista.append({
                    "Data": i.get('dataPublicacaoPncp', '')[:10],
                    "Órgão": entidade.get('razaoSocial', 'Órgão não identificado'),
                    "UF": entidade.get('uf', 'BR'),
                    "Objeto": i.get('objeto', 'Sem descrição disponível'),
                    "Valor (R$)": float(i.get('valorEstimado', 0) or 0),
                    "Link": f"https://pncp.gov.br/app/editais/{entidade.get('cnpj')}/{i.get('anoCompra')}/{i.get('sequencialId')}"
                })
            return pd.DataFrame(lista)
        
        elif response.status_code == 404:
            st.error("Erro 404: O Governo mudou o endereço da API. Tentando rota alternativa...")
            return pd.DataFrame()
        else:
            st.error(f"O servidor do governo recusou a conexão (Erro {response.status_code})")
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"Erro técnico de conexão: {e}")
        return pd.DataFrame()

# 3. Painel Lateral (Onde o seu cliente mexe)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1082/1082440.png", width=100) # Ícone genérico de engenharia
    st.header("Painel de Controle")
    termo_usuario = st.text_input("Palavra-chave para monitorar:", value="BIM")
    buscar = st.button("🚀 ATUALIZAR RADAR")
    st.markdown("---")
    st.write("**Dica de Venda:** Esta ferramenta rastreia apenas editais ativos e oficiais.")

# 4. Exibição dos Resultados
if buscar:
    with st.spinner('Escaneando portais governamentais...'):
        df = buscar_licitacoes_seguro(termo_usuario)
        
    if not df.empty:
        # Métricas de Impacto
        m1, m2, m3 = st.columns(3)
        m1.metric("Oportunidades", len(df))
        m2.metric("Ticket Médio", f"R$ {df['Valor (R$)'].mean():,.2f}")
        m3.metric("Maior Edital", f"R$ {df['Valor (R$)'].max():,.2f}")

        # Visualização por Estado
        st.subheader("🌎 Distribuição Geográfica")
        fig = px.bar(df['UF'].value_counts().reset_index(), x='UF', y='count', color='count', labels={'count':'Qtd'})
        st.plotly_chart(fig, use_container_width=True)

        # Tabela Profissional
        st.subheader("📋 Detalhamento dos Editais")
        st.dataframe(
            df, 
            column_config={"Link": st.column_config.LinkColumn("🔗 Acessar Edital")},
            use_container_width=True,
            hide_index=True
        )
        
        # Download para o cliente
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Baixar Planilha para Excel", csv, "radar_oportunidades.csv", "text/csv")
    else:
        st.warning(f"Nenhuma licitação aberta encontrada para '{termo_usuario}' neste momento.")
else:
    st.info("💡 Insira um termo (ex: BIM, Projeto, Executivo) e clique em 'Atualizar Radar'.")
