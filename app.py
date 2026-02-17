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
            # Converte para datetime
            df['data_hora'] = pd.to_datetime(df['data_hora'])
            
            # Se os dados vierem sem fuso (naive), localizamos como UTC e convertemos para Brasília
            # Se já vierem com fuso, apenas convertemos
            if df['data_hora'].dt.tz is None:
                df['data_hora'] = df['data_hora'].dt.tz_localize('UTC').dt.tz_convert(fuso_br)
            else:
                df['data_hora'] = df['data_hora'].dt.tz_convert(fuso_br)
                
            # Remove a informação de fuso para exibição limpa na tabela (opcional)
            df['data_hora'] = df['data_hora'].dt.tz_localize(None)
            
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
df = get_data()

if df.empty:
    st.warning("Nenhum dado encontrado na tabela 'controle_acesso_site'.")
    st.info("Caso precise de suporte técnico, entre em contato via [WhatsApp](https://wa.me/5511977019335?text=Olá%20Rodrigo,%20estou%20com%20problemas%20na%20visualização%20dos%20dados%20do%20dashboard).")
else:
    # --- INDICADORES PRINCIPAIS (KPIs) ---
    total_acessos = len(df)
    usuarios_unicos = df['ip'].nunique() if 'ip' in df.columns else "N/A"
    
    # Hora atual em Brasília para o KPI
    agora_br = datetime.now(fuso_br).strftime("%H:%M:%S")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Acessos", total_acessos)
    col2.metric("Visitantes Únicos (IP)", usuarios_unicos)
    col3.metric("Última Atualização", agora_br)

    # --- GRÁFICOS ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📈 Evolução Diária de Acessos")
        # Criar coluna de data para o agrupamento
        df['data'] = df['data_hora'].dt.date
        acessos_dia = df.groupby('data').size().reset_index(name='quantidade')
        fig_evolucao = px.line(acessos_dia, x='data', y='quantidade', markers=True, 
                               template="plotly_dark", color_discrete_sequence=['#00CC96'])
        st.plotly_chart(fig_evolucao, use_container_width=True)

    with c2:
        st.subheader("🌍 Origem dos Acessos (Principais Páginas/Rotas)")
        if 'pagina' in df.columns:
            top_paginas = df['pagina'].value_counts().reset_index()
            top_paginas.columns = ['Página', 'Acessos']
            fig_paginas = px.bar(top_paginas, x='Acessos', y='Página', orientation='h',
                                 template="plotly_dark", color='Acessos')
            st.plotly_chart(fig_paginas, use_container_width=True)

    # --- TABELA DE DADOS ---
    st.subheader("📝 Detalhamento dos Últimos Acessos")
    st.dataframe(df, use_container_width=True)

# --- RODAPÉ PERSONALIZADO ---
st.sidebar.image("https://via.placeholder.com/150", caption="SkyData Solution")
st.sidebar.write("### Contato")
st.sidebar.write(f"📧 [rodrigoaiosa@gmail.com](mailto:rodrigoaiosa@gmail.com)")

# Links de contato conforme diretrizes
wa_msg = "Olá Rodrigo, gostaria de conversar sobre a análise de dados do meu site."
st.sidebar.markdown(f"[💬 Falar no WhatsApp](https://wa.me/5511977019335?text={wa_msg.replace(' ', '%20')})")
st.sidebar.markdown("[📅 Agendar Reunião](https://calendly.com/rodrigoaiosa/30min)")
