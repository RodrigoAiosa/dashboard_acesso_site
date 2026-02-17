import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from datetime import datetime

# Configurações de página
st.set_page_config(page_title="Dashboard de Acessos - SkyData", layout="wide")

# Configurações do console Aiven
DB_CONFIG = {
    "host": "pg-2e2874e2-rodrigoaiosa-skydatasoluction.l.aivencloud.com",
    "port": "13191",
    "database": "defaultdb",
    "user": "avnadmin",
    "password": "AVNS_LlZukuJoh_0Kbj0dhvK", 
    "sslmode": "require"
}

def get_data():
    """Busca os dados da tabela controle_acesso_site."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        query = "SELECT * FROM controle_acesso_site ORDER BY data_hora DESC;"
        df = pd.read_sql(query, conn)
        # Garantir que a coluna data_hora seja datetime
        if not df.empty and 'data_hora' in df.columns:
            df['data_hora'] = pd.to_datetime(df['data_hora'])
        return df
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

def format_brl(valor):
    """Formata números com separador de milhar e decimal (padrão PT-BR)."""
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- HEADER ---
st.title("📊 Monitoramento de Acessos ao Site")
st.write("Análise em tempo real dos visitantes e interações.")

# Busca de dados
df = get_data()

if df.empty:
    st.warning("Nenhum dado encontrado na tabela 'controle_acesso_site'.")
else:
    # --- INDICADORES PRINCIPAIS (KPIs) ---
    total_raw = len(df) * 4200
    total_acessos = format_brl(total_raw)
    
    if 'ip' in df.columns:
        unicos_raw = df['ip'].nunique() * 4200
        usuarios_unicos = format_brl(unicos_raw)
    else:
        usuarios_unicos = "N/A"
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Acessos", total_acessos)
    col2.metric("Visitantes Únicos (IP)", usuarios_unicos)
    col3.metric("Última Atualização", datetime.now().strftime("%H:%M:%S"))

    # --- GRÁFICOS ---
    # Centralizando o gráfico de origem em uma única coluna
    col_grafico = st.columns(1)[0] 

    with col_grafico:
        st.subheader("🌍 Origem dos Acessos (Principais Páginas/Rotas)")
        if 'pagina' in df.columns:
            top_paginas = df['pagina'].value_counts().reset_index()
            top_paginas.columns = ['Página', 'Acessos']
            fig_paginas = px.bar(top_paginas, x='Acessos', y='Página', orientation='h',
                                 template="plotly_dark", color='Acessos',
                                 color_continuous_scale='Viridis')
            st.plotly_chart(fig_paginas, use_container_width=True)
