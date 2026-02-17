import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
from tabulate import tabulate

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
        # SQL com correção de fuso (-3h) e colunas para filtros
        query = """
            SELECT 
                (data_hora - INTERVAL '3 hours') as data_br,
                EXTRACT(YEAR FROM (data_hora - INTERVAL '3 hours'))::int as ano,
                EXTRACT(MONTH FROM (data_hora - INTERVAL '3 hours'))::int as mes,
                TO_CHAR(data_hora - INTERVAL '3 hours', 'YYYY-MM-DD') as data_dia,
                dispositivo, 
                navegador, 
                ip, 
                pagina, 
                acao, 
                duracao,
                id_acesso
            FROM controle_acesso_site
            WHERE duracao <> '00:00'
            ORDER BY data_br DESC;
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"❌ Erro ao conectar no banco: {e}")
        return pd.DataFrame()

# Configuração da Página Streamlit
st.set_page_config(page_title="Dashboard SkyData", layout="wide")

st.title("📊 Análise de Acessos Diários")

# Busca os dados no Banco
df = get_data()

if not df.empty:
    # --- MENU LATERAL (FILTROS) ---
    st.sidebar.header("Filtros de Período")
    
    anos_disponiveis = sorted(df['ano'].unique(), reverse=True)
    ano_selecionado = st.sidebar.selectbox("Selecione o Ano", anos_disponiveis)

    # Filtra meses baseados no ano
    df_ano = df[df['ano'] == ano_selecionado]
    meses_disponiveis = sorted(df_ano['mes'].unique())
    mes_selecionado = st.sidebar.selectbox("Selecione o Mês", meses_disponiveis)

    # Filtrando o DataFrame para o gráfico
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
            labels={'data_dia': 'Dia', 'Total de Acessos': 'Quantidade'},
            template="plotly_dark"
        )
        
        fig.update_traces(textposition="top center", line_color='#00d1b2')
        st.plotly_chart(fig, use_container_width=True)
        
        # Métrica de Resumo
        total_mes = df_filtrado.shape[0]
        st.metric("Total de Acessos no Mês Selecionado", total_mes)
    else:
        st.warning("Não há dados para o período selecionado.")

else:
    st.info("ℹ️ Nenhum registro de acesso encontrado.")

# Função para manter a compatibilidade com execução via terminal (CLI) se necessário
def ver_no_terminal():
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        query = """
            SELECT 
                id_acesso, 
                TO_CHAR(data_hora - INTERVAL '3 hours', 'DD/MM/YYYY HH24:MI:SS') as data_br,
                dispositivo, navegador, ip, pagina, acao, duracao 
            FROM controle_acesso_site
            WHERE duracao <> '00:00'
            ORDER BY data_hora DESC;
        """
        cursor.execute(query)
        linhas = cursor.fetchall()
        colunas = ["ID", "Data/Hora (BR)", "Disp.", "Navegador", "IP", "Página", "Ação", "Duração"]
        if linhas:
            print(tabulate(linhas, headers=colunas, tablefmt="grid"))
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    # Para rodar o dashboard, use: streamlit run consultar_controle_acesso_site.py
    pass
