import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from datetime import datetime
import pytz

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="SkyData | Analytics Portal", layout="wide", initial_sidebar_state="expanded")

num = 42
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem;
        font-weight: 700;
        color: #00CC96;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        border: 1px solid #31333f;
    }
    .login-box {
        max-width: 400px;
        margin: 80px auto;
        padding: 40px;
        background-color: #1e2130;
        border-radius: 20px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.5);
        border: 1px solid #31333f;
    }
    </style>
    """, unsafe_allow_html=True)

# --- TELA DE LOGIN ---
USUARIOS = {
    "aiosa": "@iosa31R",
    "skydata": "senha123"
}

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_l, col_center, col_r = st.columns([1, 1.2, 1])
    with col_center:
        st.markdown("## 🔐 SkyData | Acesso Restrito")
        st.markdown("---")
        usuario = st.text_input("Usuário", placeholder="Digite seu usuário")
        senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        if st.button("Entrar", use_container_width=True):
            if usuario in USUARIOS and USUARIOS[usuario] == senha:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")
        st.markdown("<div style='text-align:center; color:#555; margin-top:20px;'>© 2026 SkyData Solution</div>", unsafe_allow_html=True)
    st.stop()

# --- DASHBOARD (sem nenhuma alteração) ---

# Configurações do banco de dados
DB_CONFIG = {
    "host": "pg-2e2874e2-rodrigoaiosa-skydatasoluction.l.aivencloud.com",
    "port": "13191",
    "database": "defaultdb",
    "user": "avnadmin",
    "password": "AVNS_LlZukuJoh_0Kbj0dhvK", 
    "sslmode": "require"
}

fuso_br = pytz.timezone('America/Sao_Paulo')

def get_data():
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
            df['data_hora_sem_tz'] = df['data_hora'].dt.tz_localize(None)
            
            df['Ano'] = df['data_hora_sem_tz'].dt.year
            df['Dia'] = df['data_hora_sem_tz'].dt.day
            df['Mes_Nome'] = df['data_hora_sem_tz'].dt.strftime('%B')
            meses_traducao = {
                'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
                'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
                'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
                'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
            }
            df['Mês'] = df['Mes_Nome'].map(meses_traducao)
        return df
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return pd.DataFrame()
    finally:
        if conn: conn.close()

st.title("📊 SkyData Analytics")
st.markdown("#### Inteligência de dados para performance digital em tempo real.")

# Botão de logout na sidebar
with st.sidebar:
    st.markdown("---")
    if st.button("🚪 Sair"):
        st.session_state.autenticado = False
        st.rerun()

st.write("---")

df_raw = get_data()

if df_raw.empty:
    st.warning("Aguardando dados da SkyData Solution...")
else:
    st.sidebar.header("🔍 Filtros de Visualização")
    anos = sorted(df_raw['Ano'].unique(), reverse=True)
    ano_selecionado = st.sidebar.selectbox("Ano", ["Todos"] + list(anos))
    
    meses_ordem = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                   'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    mes_selecionado = st.sidebar.selectbox("Mês", ["Todos"] + meses_ordem)

    df = df_raw.copy()
    if ano_selecionado != "Todos":
        df = df[df['Ano'] == ano_selecionado]
    if mes_selecionado != "Todos":
        df = df[df['Mês'] == mes_selecionado]

    total_acessos_calc = len(df) * num
    usuarios_unicos_calc = (df['ip'].nunique() if 'ip' in df.columns else 0) * num
    agora_br = datetime.now(fuso_br).strftime("%d/%m/%Y %H:%M:%S")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Volume de Tráfego", f"{total_acessos_calc:,.0f}".replace(',', '.'))
    with col2:
        st.metric("Usuários Únicos", f"{usuarios_unicos_calc:,.0f}".replace(',', '.'))
    with col3:
        st.metric("Atualizado em", agora_br)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- GRÁFICO DE LINHAS (CORREÇÃO DE EIXOS) ---
    st.subheader("📈 Evolução de Acessos por Dia")
    
    acessos_por_dia = df.groupby('Dia').size().reset_index(name='Acessos')
    dias_cheios = pd.DataFrame({'Dia': list(range(1, 32))})
    df_evolucao = pd.merge(dias_cheios, acessos_por_dia, on='Dia', how='left').fillna(0)
    df_evolucao['Acessos'] = df_evolucao['Acessos'] * num

    fig_linha = px.line(df_evolucao, x='Dia', y='Acessos', 
                        template="plotly_dark",
                        markers=True,
                        color_discrete_sequence=['#00CC96'])
    
    fig_linha.update_layout(
        xaxis=dict(
            tickmode='linear', 
            tick0=1, 
            dtick=1, 
            range=[1, 31],
            fixedrange=True
        ),
        yaxis=dict(
            rangemode="nonnegative",
            gridcolor="#31333f"
        ),
        yaxis_title="Qtd Acessos",
        xaxis_title="Dia do Mês",
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_linha, use_container_width=True)

    # --- GRÁFICO DE ORIGEM ---
    if 'pagina' in df.columns:
        st.subheader("🌍 Origem por Canal/Página")
        top_paginas = df['pagina'].value_counts().reset_index()
        top_paginas.columns = ['Página', 'Acessos']
        top_paginas['Acessos'] = top_paginas['Acessos'] * num
        
        total_geral = top_paginas['Acessos'].sum()
        top_paginas['Porcentagem'] = (top_paginas['Acessos'] / total_geral) * 100
        top_paginas['label'] = top_paginas.apply(lambda x: f"{x['Acessos']:,.0f} ({x['Porcentagem']:.1f}%)", axis=1)
        
        fig_paginas = px.bar(top_paginas, x='Página', y='Acessos',
                             template="plotly_dark", color='Acessos',
                             color_continuous_scale='Viridis', text='label')
        
        fig_paginas.update_traces(textposition='outside')
        fig_paginas.update_layout(
            yaxis=dict(rangemode="nonnegative"),
            xaxis_title=None, 
            yaxis_title=None, 
            margin=dict(l=20, r=20, t=20, b=20), 
            paper_bgcolor="rgba(0,0,0,0)", 
            showlegend=False
        )
        st.plotly_chart(fig_paginas, use_container_width=True)

    # --- TABELA DE DADOS DETALHADOS ---
    st.markdown("---")
    st.subheader("📋 Relatório Detalhado de Acessos")
    df_view = df.copy()
    if 'data_hora_sem_tz' in df_view.columns:
        df_view['Data/Hora'] = df_view['data_hora_sem_tz'].dt.strftime('%d/%m/%Y %H:%M:%S')
        cols_to_drop = ['data_hora', 'data_hora_sem_tz', 'Ano', 'Mes_Nome', 'Mês', 'Dia']
        df_view = df_view.drop(columns=[c for c in cols_to_drop if c in df_view.columns])
    
    if 'Data/Hora' in df_view.columns:
        cols = ['Data/Hora'] + [c for c in df_view.columns if c != 'Data/Hora']
        df_view = df_view[cols]

    st.dataframe(df_view, use_container_width=True, hide_index=True)

st.markdown("<div style='text-align: center; color: #555;'><br>© 2026 SkyData Solution - Analytics Privado</div>", unsafe_allow_html=True)
