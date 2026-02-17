import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from datetime import datetime
import pytz

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

# Definição do fuso horário de Brasília
fuso_br = pytz.timezone('America/Sao_Paulo')

def get_data():
    """Busca os dados da tabela controle_acesso_site e ajusta o fuso horário."""
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        query = "SELECT * FROM controle_acesso_site ORDER BY data_hora DESC;"
        df = pd.read_sql(query, conn)
        
        if not df.empty and 'data_hora' in df.columns:
            df['data_hora'] = pd.to_datetime(df['data_hora'])
            
            if df['data_hora'].dt.tz is None:
                df['data_hora'] = df['data_hora'].dt.tz_localize('UTC').dt.tz_convert(fuso_br)
            else:
                df['data_hora'] = df['data_hora'].dt.tz_convert(fuso_br)
                
            df['data_hora'] = df['data_hora'].dt.tz_localize(None)
            
            # Colunas auxiliares para filtros
            df['Ano'] = df['data_hora'].dt.year
            df['Mes_Nome'] = df['data_hora'].dt.strftime('%B') # Nome do mês em inglês (padrão pandas)
            
            # Dicionário para tradução manual dos meses (opcional, para melhor UX)
            meses_traducao = {
                'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
                'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
                'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
                'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
            }
            df['Mês'] = df['Mes_Nome'].map(meses_traducao)
            
        return df
    except Exception as e:
        st.error(f"Erro ao conectar ao banco de dados: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

# --- HEADER ---
st.title("📊 Monitoramento de Acessos ao Site")
st.write("Análise em tempo real dos visitantes e interações.")

# Busca de dados
df_raw = get_data()

if df_raw.empty:
    st.warning("Nenhum dado encontrado na tabela 'controle_acesso_site'.")
else:
    # --- FILTROS NO MENU LATERAL ---
    st.sidebar.header("Filtros")
    
    anos = sorted(df_raw['Ano'].unique(), reverse=True)
    ano_selecionado = st.sidebar.selectbox("Selecione o Ano", ["Todos"] + list(anos))
    
    meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
             'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    mes_selecionado = st.sidebar.selectbox("Selecione o Mês", ["Todos"] + meses)

    # Aplicação dos filtros
    df = df_raw.copy()
    if ano_selecionado != "Todos":
        df = df[df['Ano'] == ano_selecionado]
    if mes_selecionado != "Todos":
        df = df[df['Mês'] == mes_selecionado]

    # --- INDICADORES PRINCIPAIS (KPIs) ---
    total_acessos = len(df)
    usuarios_unicos = df['ip'].nunique() if 'ip' in df.columns else "N/A"
    agora_br = datetime.now(fuso_br).strftime("%H:%M:%S")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Acessos", total_acessos)
    col2.metric("Visitantes Únicos (IP)", usuarios_unicos)
    col3.metric("Última Atualização", agora_br)

    # --- GRÁFICOS ---
    if not df.empty:
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("📈 Evolução Diária de Acessos")
            df['data'] = df['data_hora'].dt.date
            acessos_dia = df.groupby('data').size().reset_index(name='quantidade')
            fig_evolucao = px.line(acessos_dia, x='data', y='quantidade', markers=True, 
                                   template="plotly_dark", color_discrete_sequence=['#00CC96'])
            st.plotly_chart(fig_evolucao, use_container_width=True)

        with c2:
            st.subheader("🌍 Origem dos Acessos")
            if 'pagina' in df.columns:
                top_paginas = df['pagina'].value_counts().reset_index()
                top_paginas.columns = ['Página', 'Acessos']
                fig_paginas = px.bar(top_paginas, x='Acessos', y='Página', orientation='h',
                                     template="plotly_dark", color='Acessos')
                st.plotly_chart(fig_paginas, use_container_width=True)
    else:
        st.info("Nenhum dado disponível para os filtros selecionados.")

# Nota: O detalhamento da tabela e os itens de contato do sidebar foram removidos conforme solicitado.
