import psycopg2
import pandas as pd
import plotly.express as px
import streamlit as st
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

# --- FUNÇÃO PARA O TERMINAL (ORIGINAL) ---
def ver_controle_acesso():
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        query = """
            SELECT 
                id_acesso, 
                TO_CHAR(data_hora - INTERVAL '3 hours', 'DD/MM/YYYY HH24:MI:SS') as data_br,
                dispositivo, 
                navegador, 
                ip, 
                pagina, 
                acao, 
                duracao 
            FROM controle_acesso_site
            WHERE duracao <> '00:00'
            ORDER BY data_hora DESC;
        """
        
        cursor.execute(query)
        linhas = cursor.fetchall()
        
        colunas = ["ID", "Data/Hora (BR)", "Disp.", "Navegador", "IP", "Página", "Ação", "Duração"]
        
        print("\n=== LOG DE ACESSOS NO BD_SKYDATA (Horário de Brasília) ===")
        if linhas:
            print(tabulate(linhas, headers=colunas, tablefmt="grid"))
        else:
            print("ℹ️ Nenhum registro de acesso encontrado.")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Erro ao consultar logs: {e}")

# --- FUNÇÃO PARA O DASHBOARD (STREAMLIT) ---
def render_dashboard():
    st.set_page_config(page_title="Dashboard SkyData", layout="wide")
    st.title("📊 Análise de Acessos Diários")

    try:
        conn = psycopg2.connect(**config)
        # Query otimizada para o gráfico e filtros
        query = """
            SELECT 
                (data_hora - INTERVAL '3 hours') as data_br,
                EXTRACT(YEAR FROM (data_hora - INTERVAL '3 hours'))::int as ano,
                EXTRACT(MONTH FROM (data_hora - INTERVAL '3 hours'))::int as mes,
                TO_CHAR(data_hora - INTERVAL '3 hours', 'YYYY-MM-DD') as data_dia
            FROM controle_acesso_site
            WHERE duracao <> '00:00';
        """
        df = pd.read_sql(query, conn)
        conn.close()

        if not df.empty:
            # --- MENU LATERAL ---
            st.sidebar.header("Filtros")
            
            anos_disponiveis = sorted(df['ano'].unique(), reverse=True)
            ano_selecionado = st.sidebar.selectbox("Selecione o Ano", anos_disponiveis)

            df_ano = df[df['ano'] == ano_selecionado]
            meses_disponiveis = sorted(df_ano['mes'].unique())
            mes_selecionado = st.sidebar.selectbox("Selecione o Mês", meses_disponiveis)

            # Filtragem dos dados para o gráfico
            df_filtrado = df[(df['ano'] == ano_selecionado) & (df['mes'] == mes_selecionado)]

            # --- GRÁFICO DE LINHAS ---
            st.subheader(f"📈 Volume de Acessos - {mes_selecionado}/{ano_selecionado}")
            
            acessos_por_dia = df_filtrado.groupby('data_dia').size().reset_index(name='Total de Acessos')
            acessos_por_dia = acessos_por_dia.sort_values('data_dia')

            fig = px.line(
                acessos_por_dia, 
                x='data_dia', 
                y='Total de Acessos',
                markers=True,
                text='Total de Acessos',
                labels={'data_dia': 'Dia', 'Total de Acessos': 'Acessos'},
                template="plotly_dark"
            )
            fig.update_traces(textposition="top center", line_color='#00d1b2')
            st.plotly_chart(fig, use_container_width=True)

            # Métrica de resumo
            st.metric("Total de Acessos no Mês", len(df_filtrado))
        else:
            st.info("ℹ️ Nenhum dado para exibir no Dashboard.")

    except Exception as e:
        st.error(f"Erro no Dashboard: {e}")

# --- LÓGICA DE EXECUÇÃO ---
if __name__ == "__main__":
    import sys
    # Se o script for chamado pelo streamlit
    if "streamlit" in sys.modules or st._is_running_with_streamlit:
        render_dashboard()
    else:
        # Se for chamado via terminal comum: python app.py
        ver_controle_acesso()
