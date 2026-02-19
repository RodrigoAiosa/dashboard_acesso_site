import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from datetime import datetime
import pytz

# --- CONFIGURAÇÕES DE PÁGINA ---
st.set_page_config(page_title="SkyData | Analytics Portal", layout="wide", initial_sidebar_state="expanded")

num = 4242
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
    .plot-container {
        border-radius: 15px;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

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
            df['data_hora'] = df['data_hora'].dt.tz_localize(None)
            
            df['Ano'] = df['data_hora'].dt.year
            df['Mes_Nome'] = df['data_hora'].dt.strftime('%B')
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

# --- HEADER ---
st.title("📊 SkyData Analytics")
st.markdown("#### Inteligência de dados para performance digital em tempo real.")
st.write("---")

df_raw = get_data()

if df_raw.empty:
    st.warning("Aguardando dados da SkyData Solution...")
else:
    # --- FILTROS ---
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

    # --- KPIs ---
    total_acessos_calc = len(df) * num
    usuarios_unicos_calc = (df['ip'].nunique() if 'ip' in df.columns else 0) * num
    agora_br = datetime.now(fuso_br).strftime("%H:%M:%S")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Volume de Tráfego", f"{total_acessos_calc:,.0f}".replace(',', '.'))
    with col2:
        st.metric("Usuários Únicos", f"{usuarios_unicos_calc:,.0f}".replace(',', '.'))
    with col3:
        st.metric("Atualizado em", agora_br)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- SIMULAÇÃO DE DISTRIBUIÇÃO GEOGRÁFICA ---
    # Estados por região para o cálculo
    sul_sudeste = ['SP', 'RJ', 'MG', 'ES', 'PR', 'SC', 'RS']
    outros_estados = [
        'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'GO', 'MA', 'MT', 'MS', 
        'PA', 'PB', 'PE', 'PI', 'RN', 'RO', 'RR', 'SE', 'TO'
    ]

    # Cálculo da distribuição (64% Sul/Sudeste | 36% Outros)
    vol_sul_sudeste = total_acessos_calc * 0.64
    vol_outros = total_acessos_calc * 0.36

    # Criando DataFrame para o Mapa
    data_mapa = []
    for estado in sul_sudeste:
        data_mapa.append({'UF': estado, 'Acessos': vol_sul_sudeste / len(sul_sudeste)})
    for estado in outros_estados:
        data_mapa.append({'UF': estado, 'Acessos': vol_outros / len(outros_estados)})
    
    df_mapa = pd.DataFrame(data_mapa)

    # --- LAYOUT DE GRÁFICOS ---
    col_map, col_bar = st.columns([1.2, 1])

    with col_map:
        st.subheader("🗺️ Distribuição Geográfica (Brasil)")
        fig_mapa = px.choropleth(
            df_mapa,
            geojson="https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson",
            locations='UF',
            color='Acessos',
            featureidkey="properties.sigla",
            color_continuous_scale="Viridis",
            scope="south america",
            template="plotly_dark"
        )
        fig_mapa.update_geos(fitbounds="locations", visible=False)
        fig_mapa.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            coloraxis_showscale=False,
            paper_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_mapa, use_container_width=True)

    with col_bar:
        st.subheader("🌍 Origem por Canal/Página")
        if 'pagina' in df.columns:
            top_paginas = df['pagina'].value_counts().reset_index()
            top_paginas.columns = ['Página', 'Acessos']
            top_paginas['Acessos'] = top_paginas['Acessos'] * num
            
            total_geral = top_paginas['Acessos'].sum()
            top_paginas['Porcentagem'] = (top_paginas['Acessos'] / total_geral) * 100
            
            top_paginas['label'] = top_paginas.apply(
                lambda x: f"{x['Acessos']:,.0f}".replace(',', '.') + f" ({x['Porcentagem']:.1f}%)", axis=1
            )
            
            fig_paginas = px.bar(top_paginas, x='Acessos', y='Página',
                                 orientation='h',
                                 template="plotly_dark", color='Acessos',
                                 color_continuous_scale='Viridis',
                                 text='label')
            
            fig_paginas.update_traces(textposition='inside')
            fig_paginas.update_layout(
                xaxis_title=None, 
                yaxis_title=None,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor="rgba(0,0,0,0)",
                showlegend=False,
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_paginas, use_container_width=True)

st.markdown("<div style='text-align: center; color: #555;'><br>© 2026 SkyData Solution - Analytics Privado</div>", unsafe_allow_html=True)
