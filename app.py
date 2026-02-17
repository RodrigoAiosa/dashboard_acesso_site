import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px

# Configurações do seu console Aiven
config = {
    "host": "pg-2e2874e2-rodrigoaiosa-skydatasoluction.l.aivencloud.com",
    "port": "13191",
    "database": "defaultdb",
    "user": "avnadmin",
    "password": "AVNS_LlZukuJoh_0Kbj0dhvK", 
    "sslmode": "require"
}

def get_data():
    try:
        conn = psycopg2.connect(**config)
        # Query que já traz os dados com fuso de Brasília e colunas de suporte para o filtro
        query = """
            SELECT 
                id_acesso, 
                (data_hora - INTERVAL '3 hours') as data_br,
                EXTRACT(YEAR FROM (data_hora - INTERVAL '3 hours'))::int as ano,
                EXTRACT(MONTH FROM (data_hora - INTERVAL '3 hours'))::int as mes,
                TO_CHAR(data_hora - INTERVAL '3 hours', 'YYYY-MM-DD') as data_dia,
                dispositivo, 
                navegador, 
                ip, 
                pagina, 
                acao, 
                duracao 
            FROM controle_acesso_site
            WHERE duracao <> '00:00'
            ORDER BY data_br DESC;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erro ao conectar no banco: {e}")
        return pd.DataFrame()

# Configuração da Página
st.set_page_config(page_title="Dashboard SkyData", layout="wide")

st.title("📊 Controle de Acessos - BD_SKYDATA")

# Busca os dados
df = get_data()

if not df.empty:
    # --- MENU LATERAL ---
    st.sidebar.header("Filtros")
    
    anos_disponiveis = sorted(df['ano'].unique(), reverse=True)
    ano_selecionado = st.sidebar.selectbox("Selecione o Ano", anos_disponiveis)

    meses_disponiveis = sorted(df[df['ano'] == ano_selecionado]['mes'].unique())
    mes_selecionado = st.sidebar.selectbox("Selecione o Mês", meses_disponiveis)

    # Filtrando o DataFrame com base na escolha do usuário
    df_filtrado = df[(df['ano'] == ano_selecionado) & (df['mes'] == mes_selecionado)]

    # --- GRÁFICO DE ACESSOS POR DIA ---
    st.subheader(f"📈 Acessos Diários - {mes_selecionado}/{ano_selecionado}")
    
    # Agrupando acessos por dia
    acessos_por_dia = df_filtrado.groupby('data_dia').size().reset_index(name='Total de Acessos')
    acessos_por_dia = acessos_por_dia.sort_values('data_dia')

    fig = px.line(
        acessos_por_dia, 
        x='data_dia', 
        y='Total de Acessos',
        markers=True,
        labels={'data_dia': 'Dia do Acesso', 'Total de Acessos': 'Quantidade'},
        template="plotly_dark"
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- TABELA DE LOGS ---
    st.subheader("📋 Detalhes dos Acessos (Fuso Brasília)")
    
    # Formatando para exibição
    df_display = df_filtrado.copy()
    df_display['data_br'] = df_display['data_br'].dt.strftime('%d/%m/%Y %H:%M:%S')
    
    st.dataframe(
        df_display[['id_acesso', 'data_br', 'dispositivo', 'navegador', 'ip', 'pagina', 'acao', 'duracao']], 
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("Nenhum dado encontrado para exibir.")

# Créditos e Link WhatsApp (conforme solicitado)
st.sidebar.markdown("---")
whatsapp_link = f"https://wa.me/5511977019335?text=Olá%20Rodrigo,%20vi%20o%20dashboard%20de%20acessos%20e%20gostaria%20de%20falar%20sobre%20o%20projeto."
st.sidebar.markdown(f"[📩 Contato via WhatsApp]({whatsapp_link})")
