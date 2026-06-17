import base64
from pathlib import Path
from datetime import datetime

import gspread
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from google.oauth2.service_account import Credentials

# =========================================================
# CONFIGURAÇÃO PRINCIPAL
# =========================================================

st.set_page_config(
    page_title="SkoobPet Dashboard",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

SPREADSHEET_ID = "1Q0mLvOBxEGCojUITBLxCXRTpXVMAHE3ngvGsa2Cgf9Q"
SHEET_NAME = "Clear"

LOGIN_USER = "admin"
LOGIN_PASS = "skoobpet2026"

LOGO_FILE = "skoobpet.png"
PETS_LOGIN_FILE = "pets_login.png"

# =========================================================
# CORES SKOOBPET
# =========================================================

NAVY = "#05045C"
NAVY_2 = "#11147A"
PINK = "#D6006F"
PINK_2 = "#FF0A83"
LIGHT_BG = "#FFF7FC"
CARD = "#FFFFFF"
TEXT = "#05045C"
MUTED = "#6B6B8D"
GREEN = "#00A86B"
RED = "#E53935"
YELLOW = "#F5B400"
BORDER = "rgba(5, 4, 92, 0.10)"
SHADOW = "0 10px 30px rgba(5, 4, 92, 0.10)"

# =========================================================
# FUNÇÕES DE IMAGEM
# =========================================================


def image_to_base64(path: str) -> str:
    file = Path(path)
    if file.exists():
        return base64.b64encode(file.read_bytes()).decode("utf-8")
    return ""


def image_html(path: str, style: str = "") -> str:
    b64 = image_to_base64(path)
    if not b64:
        return ""
    return f'<img src="data:image/png;base64,{b64}" style="{style}">'


# =========================================================
# CSS GLOBAL
# =========================================================

st.markdown(
    f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    * {{
        font-family: 'Inter', sans-serif;
    }}

    .stApp {{
        background: linear-gradient(135deg, #fff8fc 0%, #f8f0ff 50%, #ffffff 100%);
        color: {TEXT};
    }}

    header[data-testid="stHeader"] {{
        background: transparent;
    }}

    [data-testid="stToolbar"] {{
        right: 1rem;
    }}

    .block-container {{
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 100%;
    }}

    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {NAVY} 0%, #07075f 55%, #030236 100%);
        border-right: 0;
    }}

    [data-testid="stSidebar"] * {{
        color: white !important;
    }}

    h1, h2, h3 {{
        color: {TEXT};
        letter-spacing: -0.04em;
    }}

    h1 {{
        font-size: 30px !important;
        font-weight: 900 !important;
        margin-bottom: 0.15rem !important;
    }}

    h2, h3 {{
        font-weight: 850 !important;
    }}

    div[data-testid="stMetric"] {{
        background: white;
        padding: 18px;
        border-radius: 16px;
        border: 1px solid {BORDER};
        box-shadow: {SHADOW};
    }}

    .card {{
        background: {CARD};
        border-radius: 18px;
        padding: 20px;
        box-shadow: {SHADOW};
        border: 1px solid {BORDER};
    }}

    .metric-card {{
        background: white;
        border-radius: 18px;
        padding: 20px;
        box-shadow: {SHADOW};
        border: 1px solid rgba(214, 0, 111, 0.10);
        min-height: 128px;
    }}

    .metric-icon {{
        width: 28px;
        height: 28px;
        border-radius: 9px;
        background: rgba(214, 0, 111, 0.08);
        color: {PINK};
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 15px;
        margin-bottom: 8px;
    }}

    .metric-title {{
        color: {MUTED};
        font-size: 13px;
        font-weight: 800;
        margin-bottom: 7px;
    }}

    .metric-value {{
        color: {TEXT};
        font-size: 29px;
        font-weight: 950;
        line-height: 1.1;
    }}

    .metric-sub {{
        color: {GREEN};
        font-size: 12px;
        font-weight: 700;
        margin-top: 10px;
    }}

    .metric-sub.red {{
        color: {RED};
    }}

    .page-location {{
        color: {PINK};
        font-size: 13px;
        font-weight: 800;
        margin-top: -2px;
        margin-bottom: 20px;
    }}

    .sidebar-logo {{
        text-align: center;
        margin: 8px 0 26px 0;
    }}

    .sidebar-logo img {{
        width: 122px;
        max-width: 80%;
    }}

    .sidebar-fallback {{
        font-size: 24px;
        font-weight: 900;
        text-align: center;
        color: white;
        margin-bottom: 30px;
    }}

    .stRadio [role="radiogroup"] {{
        gap: 10px;
    }}

    .stRadio label {{
        background: transparent;
        border-radius: 12px;
        padding: 10px 12px !important;
        transition: all 0.2s ease;
    }}

    .stRadio label:hover {{
        background: rgba(255,255,255,0.10);
    }}

    .stButton > button {{
        background: linear-gradient(90deg, {NAVY_2}, {PINK});
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.72rem 1.5rem;
        font-weight: 800;
        box-shadow: 0 8px 22px rgba(214, 0, 111, 0.20);
    }}

    .stButton > button:hover {{
        opacity: 0.94;
        color: white;
        border: none;
    }}

    .stTextInput input, .stTextArea textarea, .stNumberInput input, .stDateInput input {{
        border-radius: 12px !important;
        border: 1px solid rgba(5,4,92,0.12) !important;
        background: #FAFBFF !important;
    }}

    div[data-baseweb="select"] > div {{
        border-radius: 12px !important;
        border-color: rgba(5,4,92,0.12) !important;
        background: #FAFBFF !important;
    }}

    .table-card {{
        background: white;
        border-radius: 18px;
        padding: 18px;
        box-shadow: {SHADOW};
        border: 1px solid {BORDER};
    }}

    .step-wrapper {{
        background: white;
        border-radius: 16px;
        padding: 16px 22px;
        box-shadow: {SHADOW};
        border: 1px solid {BORDER};
        margin-bottom: 18px;
    }}

    .steps {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        align-items: center;
    }}

    .step {{
        display: flex;
        align-items: center;
        gap: 10px;
        color: {MUTED};
        font-size: 13px;
        font-weight: 800;
    }}

    .step-dot {{
        width: 28px;
        height: 28px;
        border-radius: 50%;
        background: #EEF0F7;
        color: {MUTED};
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: 900;
    }}

    .step.active {{
        color: {PINK};
    }}

    .step.active .step-dot {{
        background: {PINK};
        color: white;
    }}

    .summary-box {{
        background: white;
        border-radius: 18px;
        padding: 20px;
        box-shadow: {SHADOW};
        border: 1px solid {BORDER};
        min-height: 385px;
    }}

    .summary-title {{
        font-size: 17px;
        font-weight: 900;
        color: {TEXT};
        margin-bottom: 20px;
    }}

    .summary-label {{
        font-size: 12px;
        font-weight: 800;
        color: {MUTED};
        margin-top: 14px;
    }}

    .summary-value {{
        font-size: 14px;
        color: {TEXT};
        font-weight: 800;
        margin-top: 4px;
    }}

    .summary-total {{
        font-size: 30px;
        color: {TEXT};
        font-weight: 950;
        margin-top: 10px;
    }}

    .thin-line {{
        border-top: 1px solid rgba(5,4,92,0.10);
        margin: 18px 0;
    }}

    .login-shell {{
        width: 100%;
        min-height: calc(100vh - 50px);
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 34px;
        align-items: stretch;
        padding: 0;
    }}

    .login-left {{
        min-height: calc(100vh - 70px);
        position: relative;
        overflow: hidden;
        border-radius: 18px;
        background: linear-gradient(135deg, rgba(255,255,255,0.75), rgba(255,247,252,0.72));
        display: flex;
        justify-content: center;
        align-items: flex-start;
        text-align: center;
        box-shadow: {SHADOW};
        border: 1px solid rgba(255,255,255,0.65);
    }}

    .login-left-content {{
        margin-top: 118px;
        z-index: 3;
        position: relative;
    }}

    .login-logo img {{
        width: 245px;
        max-width: 82%;
        margin-bottom: 18px;
    }}

    .login-logo-fallback {{
        color: {NAVY};
        font-size: 42px;
        font-weight: 950;
        margin-bottom: 20px;
    }}

    .login-title {{
        color: {PINK};
        font-size: 20px;
        font-weight: 900;
        margin-bottom: 18px;
    }}

    .login-text {{
        color: {NAVY};
        font-size: 14px;
        line-height: 1.55;
        font-weight: 600;
    }}

    .login-pets {{
        position: absolute;
        left: 0;
        bottom: 0;
        width: 50%;
        max-width: 420px;
        z-index: 2;
    }}

    .login-pets-placeholder {{
        position: absolute;
        left: 24px;
        bottom: 0;
        font-size: 146px;
        line-height: 0.9;
        filter: drop-shadow(0 12px 22px rgba(5,4,92,0.14));
        z-index: 2;
    }}

    .paw-big {{
        position: absolute;
        left: -64px;
        bottom: 135px;
        width: 125px;
        height: 125px;
        border-radius: 50%;
        background: rgba(86, 0, 150, 0.06);
        z-index: 1;
    }}

    .paw-big:before {{
        content: "";
        position: absolute;
        top: -52px;
        left: 18px;
        width: 38px;
        height: 55px;
        border-radius: 50%;
        background: rgba(86, 0, 150, 0.07);
        box-shadow: 53px 4px rgba(86, 0, 150, 0.07), 97px 38px rgba(86, 0, 150, 0.07), 116px 95px rgba(86,0,150,0.06);
    }}

    .paw-small {{
        position: absolute;
        right: 68px;
        bottom: 92px;
        width: 70px;
        height: 70px;
        border-radius: 50%;
        background: rgba(86, 0, 150, 0.05);
        z-index: 1;
    }}

    .paw-small:before {{
        content: "";
        position: absolute;
        top: -32px;
        left: 10px;
        width: 22px;
        height: 31px;
        border-radius: 50%;
        background: rgba(86, 0, 150, 0.06);
        box-shadow: 31px 2px rgba(86, 0, 150, 0.06), 57px 22px rgba(86, 0, 150, 0.06);
    }}

    .login-footer {{
        position: absolute;
        right: 80px;
        bottom: 42px;
        color: {NAVY};
        font-size: 12px;
        font-weight: 600;
        z-index: 3;
    }}

    .login-right {{
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: calc(100vh - 70px);
    }}

    .login-card {{
        background: white;
        border-radius: 18px;
        padding: 38px;
        max-width: 460px;
        width: 100%;
        box-shadow: {SHADOW};
        border: 1px solid rgba(5,4,92,0.09);
    }}

    .login-card h2 {{
        color: {NAVY};
        font-size: 22px;
        font-weight: 950;
        margin-bottom: 26px;
    }}

    .login-options {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        align-items: center;
        gap: 8px;
        margin: 4px 0 18px 0;
    }}

    .forgot-text {{
        color: {PINK};
        text-align: right;
        font-size: 12px;
        font-weight: 800;
        margin-top: 8px;
    }}

    @media (max-width: 950px) {{
        .login-shell {{
            grid-template-columns: 1fr;
        }}
        .login-left {{
            min-height: 560px;
        }}
        .login-right {{
            min-height: auto;
        }}
    }}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# GOOGLE SHEETS
# =========================================================


@st.cache_resource
def get_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes,
    )

    return gspread.authorize(credentials)


@st.cache_data(ttl=60)
def load_data():
    client = get_client()
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    rows = sheet.get_all_records()
    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df.columns = [str(c).strip() for c in df.columns]

    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    if "Data Compra" in df.columns:
        df["Data Compra"] = pd.to_datetime(df["Data Compra"], dayfirst=True, errors="coerce")

    if "Valor" in df.columns:
        df["Valor"] = (
            df["Valor"]
            .astype(str)
            .str.replace("R$", "", regex=False)
            .str.replace(".", "", regex=False)
            .str.replace(",", ".", regex=False)
        )
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    else:
        df["Valor"] = 0

    if "Unidade" in df.columns:
        df = df[df["Unidade"].str.upper().str.contains("CAMPINAS", na=False)]

    return df


def append_row(data):
    client = get_client()
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
    sheet.append_row(data, value_input_option="USER_ENTERED")
    st.cache_data.clear()


# =========================================================
# LOGIN
# =========================================================


def login_page():
    logo = image_html(LOGO_FILE, "width:245px; max-width:82%; margin-bottom:18px;")
    pets_b64 = image_to_base64(PETS_LOGIN_FILE)

    if logo:
        logo_html = f'<div class="login-logo">{logo}</div>'
    else:
        logo_html = '<div class="login-logo-fallback">SkoobPet</div>'

    if pets_b64:
        pets_html = f'<img class="login-pets" src="data:image/png;base64,{pets_b64}">'
    else:
        pets_html = '<div class="login-pets-placeholder">🐶🐱</div>'

    left, right = st.columns([1.05, 1])

    with left:
        st.markdown(
            f"""
            <div class="login-left">
                <div class="paw-big"></div>
                <div class="paw-small"></div>

                <div class="login-left-content">
                    {logo_html}
                    <div class="login-title">Bem-vindo(a) de volta!</div>
                    <div class="login-text">
                        Faça login para acessar o<br>
                        painel da SkoobPet e acompanhar<br>
                        os resultados da unidade<br>
                        Campinas.
                    </div>
                </div>

                {pets_html}
                <div class="login-footer">© 2026 SkoobPet. Todos os direitos reservados.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.markdown('<div class="login-right">', unsafe_allow_html=True)
        st.markdown('<div class="login-card">', unsafe_allow_html=True)

        st.markdown("<h2>Acessar conta</h2>", unsafe_allow_html=True)

        user = st.text_input("Usuário", placeholder="Digite seu usuário")
        password = st.text_input("Senha", type="password", placeholder="Digite sua senha")

        opt1, opt2 = st.columns([1, 1])
        with opt1:
            st.checkbox("Lembrar de mim")
        with opt2:
            st.markdown('<div class="forgot-text">Esqueci minha senha</div>', unsafe_allow_html=True)

        if st.button("Entrar", use_container_width=True):
            if user == LOGIN_USER and password == LOGIN_PASS:
                st.session_state["logged"] = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# SIDEBAR
# =========================================================


def sidebar():
    with st.sidebar:
        logo = image_html(LOGO_FILE, "width:125px; max-width:82%;")
        if logo:
            st.markdown(f'<div class="sidebar-logo">{logo}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="sidebar-fallback">🐶🐱<br>SkoobPet</div>', unsafe_allow_html=True)

        page = st.radio(
            "Menu",
            ["Visão geral", "Formulário", "Financeiro"],
            label_visibility="collapsed",
        )

        st.markdown("<br><br><br><br><br><br><br>", unsafe_allow_html=True)

        if st.button("Sair"):
            st.session_state["logged"] = False
            st.rerun()

    return page


# =========================================================
# COMPONENTES
# =========================================================


def metric_card(title, value, sub="↑ Período selecionado", icon="🐾", negative=False):
    red_class = " red" if negative else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-icon">{icon}</div>
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub{red_class}">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def money(value):
    try:
        value = float(value)
    except Exception:
        value = 0
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def filter_period(df):
    if df.empty or "Data Compra" not in df.columns:
        return df

    valid_dates = df["Data Compra"].dropna()

    if valid_dates.empty:
        return df

    min_date = valid_dates.min().date()
    max_date = valid_dates.max().date()

    period = st.date_input(
        "Período",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if isinstance(period, tuple) and len(period) == 2:
        start, end = period
        df = df[
            (df["Data Compra"].dt.date >= start)
            & (df["Data Compra"].dt.date <= end)
        ]

    return df


def get_status_column(df):
    for col in ["Status", "Status Venda Pedigree", "Status Venda", "Situação", "Situacao"]:
        if col in df.columns:
            return col
    return None


def get_seller_column(df):
    for col in ["Vendedora", "Vendedor", "Responsável", "Responsavel", "Consultora"]:
        if col in df.columns:
            return col
    return None


def get_payment_column(df):
    for col in ["Forma de Pagamento", "Pagamento", "Forma Pagamento", "Forma de pagamento"]:
        if col in df.columns:
            return col
    return None


# =========================================================
# VISÃO GERAL
# =========================================================


def page_overview(df):
    top1, top2 = st.columns([1, 0.32])
    with top1:
        st.title("Visão geral")
        st.markdown('<div class="page-location">📍 Campinas</div>', unsafe_allow_html=True)
    with top2:
        df = filter_period(df)

    total_contatos = len(df)
    total_vendas = len(df)
    faturamento = df["Valor"].sum() if "Valor" in df.columns else 0
    ticket = faturamento / total_vendas if total_vendas else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Contatos no mês", total_contatos, "↑ Unidade Campinas", "☘")
    with c2:
        metric_card("Vendas no mês", total_vendas, "↑ Período selecionado", "🛒")
    with c3:
        metric_card("Ticket médio", money(ticket), "↑ Média por venda", "💳")
    with c4:
        metric_card("Faturamento no mês", money(faturamento), "↑ Total vendido", "💰")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.2, 1.2, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Contatos por dia")
        if "Data Compra" in df.columns and not df.empty:
            chart = df.groupby(df["Data Compra"].dt.date).size().reset_index(name="Contatos")
            fig = px.line(chart, x="Data Compra", y="Contatos", markers=True)
            fig.update_traces(line_color=PINK, marker_color=PINK)
            fig.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10), plot_bgcolor="white", paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados para exibir.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Vendas por dia")
        if "Data Compra" in df.columns and not df.empty:
            chart = df.groupby(df["Data Compra"].dt.date)["Valor"].sum().reset_index()
            fig = px.line(chart, x="Data Compra", y="Valor", markers=True)
            fig.update_traces(line_color=NAVY_2, marker_color=NAVY_2)
            fig.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10), plot_bgcolor="white", paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados para exibir.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Vendas por unidade")
        fig = go.Figure(data=[go.Pie(labels=["Campinas"], values=[100], hole=0.58, marker=dict(colors=[PINK]))])
        fig.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10), paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col4, col5, col6 = st.columns([1.2, 1.2, 1])

    with col4:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Raças mais vendidas")
        if "Raça" in df.columns and not df.empty:
            chart = df["Raça"].replace("", "Não informado").value_counts().head(8).reset_index()
            chart.columns = ["Raça", "Quantidade"]
            fig = px.bar(chart, x="Quantidade", y="Raça", orientation="h", text="Quantidade")
            fig.update_traces(marker_color=PINK, textposition="outside")
            fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10), plot_bgcolor="white", paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Coluna Raça não encontrada.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col5:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Vendas por vendedora")
        seller_col = get_seller_column(df)
        if seller_col and not df.empty:
            chart = df[seller_col].replace("", "Não informado").value_counts().head(8).reset_index()
            chart.columns = ["Vendedora", "Quantidade"]
            fig = px.bar(chart, x="Vendedora", y="Quantidade", text="Quantidade")
            fig.update_traces(marker_color=PINK, textposition="outside")
            fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10), plot_bgcolor="white", paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Coluna de vendedora não encontrada.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col6:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Resumo por status")
        status_col = get_status_column(df)
        if status_col and not df.empty:
            status = df[status_col].replace("", "Sem status").value_counts().reset_index()
            status.columns = ["Status", "Quantidade"]
            status["%"] = (status["Quantidade"] / status["Quantidade"].sum() * 100).round(1).astype(str) + "%"
            st.dataframe(status, use_container_width=True, hide_index=True)
        else:
            st.info("Sem coluna de status.")
        st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# FORMULÁRIO
# =========================================================


def page_form(df):
    st.title("Formulário")
    st.markdown('<div class="page-location">📍 Campinas</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="step-wrapper">
            <div class="steps">
                <div class="step active"><div class="step-dot">1</div>Dados do cliente</div>
                <div class="step"><div class="step-dot">2</div>Informações</div>
                <div class="step"><div class="step-dot">3</div>Produtos/Serviços</div>
                <div class="step"><div class="step-dot">4</div>Conclusão</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    form_col, summary_col = st.columns([2.15, 0.9])

    with form_col:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Dados do cliente")

        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome completo", placeholder="Digite o nome do cliente")
            email = st.text_input("E-mail", placeholder="email@exemplo.com")
            cpf = st.text_input("CPF", placeholder="000.000.000-00")
            raca = st.text_input("Raça", placeholder="Digite a raça")
        with c2:
            telefone = st.text_input("Telefone", placeholder="(19) 99999-9999")
            data_compra = st.date_input("Data da compra", value=datetime.today())
            sexo = st.selectbox("Sexo", ["", "MACHO", "FÊMEA"])
            cor = st.text_input("Cor", placeholder="Digite a cor")

        observacoes = st.text_area("Observações", placeholder="Digite observações adicionais...")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Dados da venda")

        c3, c4, c5 = st.columns(3)
        with c3:
            valor = st.number_input("Valor", min_value=0.0, step=10.0)
        with c4:
            vendedora = st.text_input("Vendedora")
        with c5:
            status = st.selectbox(
                "Status",
                ["Novo Lead", "Conversando", "Sem interesse", "Aguardando", "Fechado", "Pago", "Pendente"],
            )

        b1, b2, b3 = st.columns([1, 1, 1])
        with b2:
            cancelar = st.button("Cancelar", use_container_width=True)
        with b3:
            salvar = st.button("Salvar atendimento →", use_container_width=True)

        if cancelar:
            st.rerun()

        if salvar:
            mes = data_compra.strftime("%m/%Y")
            new_row = [
                nome,
                telefone,
                cpf,
                email,
                data_compra.strftime("%d/%m/%Y"),
                mes,
                raca,
                sexo,
                cor,
                valor,
                vendedora,
                "Campinas",
                status,
                observacoes,
            ]
            append_row(new_row)
            st.success("Atendimento salvo com sucesso!")

        st.markdown("</div>", unsafe_allow_html=True)

    with summary_col:
        st.markdown('<div class="summary-box">', unsafe_allow_html=True)
        st.markdown('<div class="summary-title">Resumo do atendimento</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-label">Cliente</div><div class="summary-value">{nome or "-"}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-label">Raça</div><div class="summary-value">{raca or "-"}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-label">Vendedora</div><div class="summary-value">{vendedora or "-"}</div>', unsafe_allow_html=True)
        st.markdown('<div class="thin-line"></div>', unsafe_allow_html=True)
        st.markdown('<div class="summary-label">Total</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="summary-total">{money(valor)}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="table-card">', unsafe_allow_html=True)
    st.subheader("Histórico de atendimentos")

    if not df.empty:
        busca = st.text_input("Buscar cliente", placeholder="Digite o nome do cliente")
        show_df = df.copy()
        if busca and "Nome" in show_df.columns:
            show_df = show_df[show_df["Nome"].str.contains(busca, case=False, na=False)]
        st.dataframe(show_df.tail(20), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum atendimento encontrado.")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# FINANCEIRO
# =========================================================


def page_financial(df):
    top1, top2 = st.columns([1, 0.32])
    with top1:
        st.title("Financeiro")
        st.markdown('<div class="page-location">📍 Campinas</div>', unsafe_allow_html=True)
    with top2:
        df = filter_period(df)

    faturamento = df["Valor"].sum() if "Valor" in df.columns else 0
    recebido = faturamento
    pendente = 0
    vendas = len(df)

    status_col = get_status_column(df)
    if status_col and not df.empty:
        pendente_df = df[df[status_col].str.upper().str.contains("PENDENTE|AGUARDANDO", na=False)]
        pendente = pendente_df["Valor"].sum()
        recebido = faturamento - pendente

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Faturamento bruto", money(faturamento), "↑ Período selecionado", "💰")
    with c2:
        metric_card("Recebido", money(recebido), "↑ Valores pagos", "✅")
    with c3:
        metric_card("Pendente", money(pendente), "↓ A receber", "⏳", negative=True)
    with c4:
        metric_card("Nº de vendas", vendas, "↑ Total de registros", "🧾")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.6, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Faturamento ao longo do tempo")
        if "Data Compra" in df.columns and not df.empty:
            chart = df.groupby(df["Data Compra"].dt.date)["Valor"].sum().reset_index()
            fig = px.area(chart, x="Data Compra", y="Valor")
            fig.update_traces(line_color=PINK, fillcolor="rgba(214,0,111,0.18)")
            fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10), plot_bgcolor="white", paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados para exibir.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Forma de pagamento")
        pay_col = get_payment_column(df)
        if pay_col and not df.empty:
            chart = df[pay_col].replace("", "Não informado").value_counts().reset_index()
            chart.columns = ["Forma", "Quantidade"]
            fig = px.pie(chart, names="Forma", values="Quantidade", hole=0.55)
            fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10), paper_bgcolor="white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Coluna de pagamento não encontrada.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="table-card">', unsafe_allow_html=True)
    st.subheader("Últimas vendas")
    if not df.empty:
        st.dataframe(df.tail(10), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma venda encontrada.")
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# MAIN
# =========================================================


def main():
    if "logged" not in st.session_state:
        st.session_state["logged"] = False

    if not st.session_state["logged"]:
        login_page()
        return

    page = sidebar()

    try:
        df = load_data()
    except Exception as error:
        st.error(
            "Erro ao carregar a planilha. Verifique o secrets.toml e se a planilha foi compartilhada com o e-mail da conta de serviço."
        )
        st.exception(error)
        return

    if page == "Visão geral":
        page_overview(df)
    elif page == "Formulário":
        page_form(df)
    elif page == "Financeiro":
        page_financial(df)


if __name__ == "__main__":
    main()
