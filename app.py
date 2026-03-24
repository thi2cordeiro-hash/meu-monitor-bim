import streamlit as st
import pandas as pd
import requests
import plotly.express as px

st.set_page_config(page_title="BIM Radar Pro", layout="wide", page_icon="🏗️")

# Interface Profissional
st.title("🏗️ BIM Radar: Monitor de Oportunidades")
st.markdown("---")

@st.cache_data(ttl=300)
def buscar_licitacoes_v3(termo):
    # ROTA DE CONSULTA (A que o site oficial usa para listar os cards)
    url = "https://pncp.gov.br/api/consulta/v1/contratacoes"
    
    params = {
        "pagina": 1,
        "tamanhoPagina": 50,
        "termo": termo,
        "ordem": "dataPublicacao",
        "direcao": "desc"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://pncp.gov.br/app/editais",
        "Origin": "https://pncp.gov.br"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=20)
        
        # LOG DE DIAGNÓSTICO (Ajuda a gente a saber o que houve)
        if response.status_code == 200:
            dados = response.json()
            items = dados.get('data', []) # A nova API coloca os resultados em 'data'
            
            if not items:
                return pd.DataFrame()

            resultados = []
            for i in items:
                entidade = i.get('orgaoEntidade', {})
                # Link formatado corretamente para o novo padrão
                link = f"https://pncp.gov.br/app/editais/{entidade.get('cnpj')}/{i.get('anoCompra')}/{i.get('sequencialId')}"
                
                resultados.append({
                    "Data": i.get('dataPublicacaoPncp', '')[:10],
                    "Órgão": entidade.get('razaoSocial', 'N/A'),
                    "UF": entidade.get('uf', 'BR'),
                    "Objeto": i.get('objeto', ''),
                    "Valor (R$)": float(i.get('valorEstimado', 0) or 0),
                    "Link": link
                })
            return pd.DataFrame(resultados)
        else:
            return response.status_code # Retorna o erro para exibir na tela
    except Exception as e:
        return str(e)

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("🔍 Filtros de Busca")
    termo_input = st.text_input("Palavra-chave:", value="BIM")
    buscar_btn = st.button("🚀 Pesquisar")

if buscar_btn:
    resultado = buscar_licitacoes_v3(termo_input)
    
    if isinstance(resultado, pd.DataFrame):
        if not resultado.empty:
            # Métricas
            c1, c2, c3 = st.columns(3)
            c1.metric("Editais", len(resultado))
            c2.metric("Média", f"R$ {resultado['Valor (R$)'].mean():,.2f}")
            c3.metric("Máximo", f"R$ {resultado['Valor (R$)'].max():,.2f}")

            # Gráfico
            st.plotly_chart(px.bar(resultado['UF'].value_counts().reset_index(), x='UF', y='count'), use_container_width=True)

            # Tabela
            st.dataframe(resultado, column_config={"Link": st.column_config.LinkColumn("🔗 Abrir")}, use_container_width=True)
        else:
            st.warning("Nenhum edital encontrado para este termo.")
    else:
        st.error(f"Erro no Servidor do Governo: {resultado}")
        st.info("Dica: O portal PNCP pode estar em manutenção. Tente novamente em 15 minutos.")
