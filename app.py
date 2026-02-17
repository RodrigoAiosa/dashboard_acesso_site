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
        # Query com ajuste de -3h para fuso de Brasília e suporte para filtros
        query = """
            SELECT 
                (data_hora - INTERVAL '3 hours') as data_br,
                EXTRACT(YEAR FROM (data_hora - INTERVAL '3 hours'))::int as ano,
                EXTRACT(MONTH FROM (data_hora - INTERVAL '3 hours'))::int as mes,
                TO_CHAR(data_hora - INTERVAL '3 hours', 'YYYY-MM-DD') as data_dia,
                id_acesso
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

st.title("📊 Análise de Acessos Diários")

# Busca os dados
df = get_data()

if not df.empty:
    # --- MENU LATERAL (FILTROS) ---
    st.sidebar.header("Filtros de Período")
    
    anos_disponiveis = sorted(df['ano'].unique(), reverse=True)
    ano_selecionado = st.sidebar.selectbox("Selecione o Ano", anos_disponiveis)

    # Filtra os meses disponíveis para o ano selecionado
    df_ano = df[df['ano'] == ano_selecionado]
    meses_disponiveis = sorted(df_ano['mes'].unique())
    
    # Dicionário para exibir nomes dos meses em vez de números, se preferir
    mes_selecionado = st.sidebar.selectbox("Selecione o Mês", meses_disponiveis)

    # Filtrando o DataFrame final para o gráfico
    df_filtrado = df[(df['ano'] == ano_selecionado) & (df['mes'] == mes_selecionado)]

    # --- GRÁFICO DE ACESSOS POR DIA ---
    if not df_filtrado.empty:
        st.subheader(f"📈 Volume de Acessos em {mes_selecionado}/{ano_selecionado}")
        
        # Agrupando acessos por dia
        acessos_por_dia = df_filtrado.groupby('data_dia').size().reset_index(name='Total de Acessos')
        acessos_por_dia = acessos_por_dia.sort_values('data_dia')

        fig = px.line(
            acessos_por_dia, 
            x='data_dia', 
            y='Total de Acessos',
            markers=True,
            text='Total de Acessos',
            labels={'data_dia': 'Dia', 'Total de Acessos': 'Quantidade de Acessos'},
            template="plotly_dark"
        )
        
        fig.update_traces(textposition="top center", line_color='#00d1b2')
        st.plotly_chart(fig, use_container_width=True)
        
        # Métrica simples de resumo
        total_mes = df_filtrado.shape[0]
        st.metric("Total de Acessos no Mês Selecionado", total_mes)
    else:
        st.warning("Não há dados para o período selecionado.")

else:
    st.info("Nenhum registro de acesso encontrado no banco de dados.")
