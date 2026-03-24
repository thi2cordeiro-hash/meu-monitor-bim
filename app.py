def buscar_licitacoes_seguro(termo_busca):
    # Rota de consulta simplificada (Mais estável que a de contratações direta)
    url = "https://pncp.gov.br/api/consulta/v1/contratacoes"
    
    params = {
        "pagina": 1,
        "tamanhoPagina": 10,
        "termo": termo_busca,
        "ordem": "dataPublicacao",
        "direcao": "desc"
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://pncp.gov.br/app/editais",
        "Origin": "https://pncp.gov.br"
    }

    try:
        # Aumentamos o timeout para 30 segundos porque o gov é lento
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return pd.DataFrame(response.json().get('data', []))
        else:
            # Se ainda der 404, tentamos a rota alternativa v1
            url_alt = "https://pncp.gov.br/api/pncp/v1/contratacoes"
            response = requests.get(url_alt, params=params, headers=headers, timeout=30)
            return pd.DataFrame(response.json().get('data', []))
    except:
        return pd.DataFrame()
