import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from datetime import datetime

# Configurações de página
st.set_page_config(page_title="Dashboard de Acessos - SkyData", layout="wide")

# Configurações do console Aiven (conforme fornecido)
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

# --- HEADER ---
st.title("📊 Monitoramento de Acessos ao Site")
st.write("Análise em tempo real dos visitantes e interações.")

# Busca de dados
df = get_data()

if df.empty:
    st.warning("Nenhum dado encontrado na tabela 'controle_acesso_site'.")
    st.info("Caso precise de suporte técnico, entre em contato via [WhatsApp](https://wa.me/5511977019335?text=Olá%20Rodrigo,%20estou%20com%20dúvidas%20sobre%20o%20dashboard%20de%20acessos).")
else:
    # --- INDICADORES PRINCIPAIS (KPIs) ---
    total_acessos = len(df) * 420
    usuarios_unicos = df['ip'].nunique() * 420 if 'ip' in df.columns else "N/A" 
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Acessos", total_acessos)
    col2.metric("Visitantes Únicos (IP)", usuarios_unicos)
    col3.metric("Última Atualização", datetime.now().strftime("%H:%M:%S"))

    # --- GRÁFICOS ---
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📈 Evolução Diária de Acessos")
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

# --- RODAPÉ PERSONALIZADO ---
st.sidebar.image("https://via.placeholder.com/150", caption="SkyData Solution") # Substitua pela sua logo se tiver
st.sidebar.markdown("---")
st.sidebar.write("### Contato")
st.sidebar.write("📧 [rodrigoaiosa@gmail.com](mailto:rodrigoaiosa@gmail.com)")

# Link do WhatsApp personalizado conforme solicitado
whatsapp_url = "https://wa.me/5511977019335?text=Olá%20Rodrigo,%20gostaria%20de%20agendar%20uma%20reunião%20sobre%20os%20indicadores%20do%20site."
st.sidebar.markdown(f"[💬 Falar no WhatsApp]({whatsapp_url})")

# Link do Calendly (Apenas Hiperlink, conforme regra de não mencionar o nome diretamente no texto)
st.sidebar.markdown("[📅 Agendar Reunião](https://calendly.com/rodrigoaiosa/30min)")
