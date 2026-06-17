
import base64
import re
from datetime import date

import gspread
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from google.oauth2.service_account import Credentials


# ==========================================================
# DASHBOARD SKOOBPET CAMPINAS
# Python + Streamlit + Google Sheets
# Arquivo principal: app.py
# ==========================================================

APP_TITLE = "SkoobPet Dashboard"
SHEET_ID = "1Q0mLvOBxEGCojUITBLxCXRtpXVMAHE3ngvGsa2Cgf9Q"
WORKSHEET_NAME = "Clear"
UNIDADE_FIXA = "CAMPINAS"
LOGO_PATH = "assets/skoobpet.png"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


# ==========================================================
# CORES BASEADAS NA LOGO SKOOBPET
# ==========================================================
NAVY = "#0D1464"
NAVY_2 = "#111B78"
MAGENTA = "#C50052"
MAGENTA_2 = "#E1006A"
PINK_SOFT = "#FFF4FA"
LILAC = "#F7F3FA"
WHITE = "#FFFFFF"
TEXT = "#111632"
MUTED = "#667085"
GREEN = "#0A8F4E"
RED = "#E03A3A"
BORDER = "rgba(13, 20, 100, 0.10)"


# ==========================================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================================
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==========================================================
# HELPERS
# ==========================================================
def img_base64(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return ""


def normalize_col(col):
    col = str(col).strip()
    col = re.sub(r"\s+", " ", col)
    return col


def find_col(df, names):
    lower_map = {normalize_col(c).lower(): c for c in df.columns}
    for name in names:
        key = normalize_col(name).lower()
        if key in lower_map:
            return lower_map[key]
    return None


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def clean_upper(value):
    return clean_text(value).upper()


def clean_phone(value):
    if pd.isna(value):
        return ""
    return re.sub(r"\D", "", str(value))


def parse_money(value):
    if pd.isna(value):
        return 0.0
    s = str(value).strip()
    if not s:
        return 0.0
    s = s.replace("R$", "").replace(" ", "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0


def br_money(value):
    try:
        return f"R$ {float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return "R$ 0,00"


def month_from_date(dt):
    if pd.isna(dt):
        return ""
    return f"{dt.month:02d}/{dt.year}"


def fig_style(fig, height=330):
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=15, r=15, t=15, b=15),
        font=dict(family="Inter, Arial", color=TEXT, size=12),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
        ),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(13,20,100,0.08)",
        zeroline=False,
        linecolor="rgba(13,20,100,0.08)",
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(13,20,100,0.08)",
        zeroline=False,
        linecolor="rgba(13,20,100,0.08)",
    )
    return fig


def app_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

        :root {{
            --navy: {NAVY};
            --magenta: {MAGENTA};
            --soft: {PINK_SOFT};
        }}

        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif !important;
        }}

        .stApp {{
            background:
                radial-gradient(circle at top left, rgba(197,0,82,0.08), transparent 28%),
                radial-gradient(circle at bottom right, rgba(13,20,100,0.08), transparent 30%),
                linear-gradient(135deg, #FFFFFF 0%, #FFF7FB 45%, #F8F4FB 100%);
            color: {TEXT};
        }}

        .block-container {{
            padding-top: 2.1rem;
            padding-left: 2.1rem;
            padding-right: 2.1rem;
            max-width: 1500px;
        }}

        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {NAVY} 0%, #10156D 62%, #070B3A 100%);
            border-right: 0px;
            box-shadow: 14px 0 36px rgba(13,20,100,0.16);
        }}

        section[data-testid="stSidebar"] > div {{
            padding: 22px 16px 18px 16px;
        }}

        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] div {{
            color: #ffffff !important;
        }}

        .sidebar-logo {{
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 4px 0 24px 0;
        }}

        .sidebar-logo img {{
            max-width: 158px;
            height: auto;
        }}

        div[role="radiogroup"] label {{
            background: transparent !important;
            border-radius: 14px;
            padding: 10px 12px !important;
            margin-bottom: 8px;
            min-height: 46px;
            transition: 0.2s ease;
        }}

        div[role="radiogroup"] label:hover {{
            background: rgba(255,255,255,0.08) !important;
        }}

        div[role="radiogroup"] label:has(input:checked) {{
            background: linear-gradient(135deg, {MAGENTA}, {MAGENTA_2}) !important;
            box-shadow: 0 12px 22px rgba(197,0,82,0.28);
        }}

        .sidebar-footer {{
            position: fixed;
            bottom: 24px;
            left: 24px;
            width: 160px;
            color: white;
            opacity: 0.95;
            font-size: 14px;
        }}

        h1, h2, h3 {{
            color: {NAVY};
            font-weight: 900;
            letter-spacing: -0.03em;
        }}

        .page-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 18px;
            margin-bottom: 22px;
        }}

        .title-wrap h1 {{
            margin: 0;
            font-size: 38px;
            line-height: 1.05;
            color: {NAVY};
        }}

        .location {{
            display: inline-flex;
            align-items: center;
            gap: 7px;
            color: {TEXT};
            font-weight: 600;
            font-size: 14px;
            margin-top: 8px;
        }}

        .top-actions {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .admin-pill {{
            background: white;
            border: 1px solid {BORDER};
            border-radius: 999px;
            padding: 8px 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 10px 25px rgba(13,20,100,0.06);
            font-weight: 700;
            color: {TEXT};
            white-space: nowrap;
        }}

        .avatar {{
            width: 34px;
            height: 34px;
            border-radius: 50%;
            background: {NAVY};
            color: white;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
            font-size: 12px;
        }}

        .notice-bell {{
            width: 42px;
            height: 42px;
            border-radius: 14px;
            background: white;
            border: 1px solid {BORDER};
            display: inline-flex;
            align-items: center;
            justify-content: center;
            color: {MAGENTA};
            font-size: 19px;
            box-shadow: 0 10px 25px rgba(13,20,100,0.06);
        }}

        .kpi-card {{
            background: {WHITE};
            border: 1px solid {BORDER};
            border-radius: 18px;
            padding: 22px 22px;
            min-height: 142px;
            box-shadow: 0 14px 34px rgba(13,20,100,0.08);
        }}

        .kpi-row {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 14px;
        }}

        .kpi-icon {{
            color: {MAGENTA};
            width: 36px;
            height: 36px;
            border-radius: 12px;
            background: #FFF1F7;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
        }}

        .kpi-label {{
            color: {TEXT};
            font-size: 14px;
            font-weight: 700;
        }}

        .kpi-value {{
            color: {NAVY};
            font-size: 28px;
            font-weight: 900;
            margin-bottom: 8px;
            line-height: 1;
        }}

        .kpi-trend {{
            color: {GREEN};
            font-size: 13px;
            font-weight: 800;
        }}

        .dash-card {{
            background: {WHITE};
            border: 1px solid {BORDER};
            border-radius: 18px;
            padding: 20px;
            box-shadow: 0 14px 34px rgba(13,20,100,0.08);
            margin-bottom: 18px;
        }}

        .dash-card-title {{
            color: {NAVY};
            font-size: 17px;
            font-weight: 900;
            margin-bottom: 8px;
        }}

        .dash-card-subtitle {{
            color: {MUTED};
            font-size: 13px;
            margin-top: -2px;
            margin-bottom: 12px;
        }}

        .filter-card {{
            background: {WHITE};
            border: 1px solid {BORDER};
            border-radius: 18px;
            padding: 16px;
            box-shadow: 0 14px 34px rgba(13,20,100,0.08);
            margin-bottom: 20px;
        }}

        .chip {{
            display: inline-flex;
            gap: 8px;
            align-items: center;
            background: #FFF0F7;
            border-radius: 999px;
            padding: 8px 13px;
            color: {MAGENTA};
            font-weight: 800;
            font-size: 13px;
            margin-right: 10px;
        }}

        div.stButton > button,
        div.stDownloadButton > button,
        button[kind="primary"] {{
            background: linear-gradient(135deg, {NAVY}, {MAGENTA}) !important;
            color: white !important;
            border: none !important;
            border-radius: 13px !important;
            font-weight: 800 !important;
            min-height: 42px;
            box-shadow: 0 12px 24px rgba(197,0,82,0.20);
        }}

        div.stButton > button:hover,
        div.stDownloadButton > button:hover {{
            filter: brightness(1.04);
            color: white !important;
        }}

        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stDateInput"] input,
        div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        textarea {{
            border-radius: 13px !important;
            border-color: rgba(13,20,100,0.15) !important;
            background: #FFFFFF !important;
        }}

        .form-shell {{
            background: {WHITE};
            border: 1px solid {BORDER};
            border-radius: 18px;
            padding: 24px;
            box-shadow: 0 14px 34px rgba(13,20,100,0.08);
        }}

        .stepper {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: {WHITE};
            border: 1px solid {BORDER};
            border-radius: 18px;
            padding: 16px 22px;
            box-shadow: 0 14px 34px rgba(13,20,100,0.08);
            margin-bottom: 22px;
        }}

        .step {{
            display: flex;
            align-items: center;
            gap: 9px;
            color: {MUTED};
            font-weight: 800;
            font-size: 13px;
        }}

        .step-number {{
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: #EEF0F6;
            color: {MUTED};
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
        }}

        .step.active {{
            color: {MAGENTA};
        }}

        .step.active .step-number {{
            background: {MAGENTA};
            color: white;
        }}

        .summary-box {{
            background: {WHITE};
            border: 1px solid {BORDER};
            border-radius: 18px;
            padding: 22px;
            box-shadow: 0 14px 34px rgba(13,20,100,0.08);
            min-height: 390px;
        }}

        .summary-total {{
            color: {NAVY};
            font-size: 31px;
            font-weight: 900;
            margin-top: 16px;
        }}

        .status-dot {{
            width: 11px;
            height: 11px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }}

        .login-container {{
            min-height: 90vh;
            display: grid;
            grid-template-columns: 1fr 1.05fr;
            gap: 60px;
            align-items: center;
            padding: 30px 24px;
        }}

        .login-left {{
            text-align: center;
            position: relative;
            min-height: 690px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }}

        .paw-bg {{
            position: absolute;
            font-size: 180px;
            color: rgba(197,0,82,0.05);
            left: 10px;
            top: 130px;
            transform: rotate(-20deg);
        }}

        .pet-illustration {{
            font-size: 150px;
            margin-top: 45px;
            filter: drop-shadow(0 18px 22px rgba(13,20,100,0.12));
        }}

        .login-logo {{
            width: 230px;
            margin-bottom: 28px;
        }}

        .login-title {{
            color: {MAGENTA};
            font-size: 25px;
            font-weight: 900;
            margin-bottom: 18px;
        }}

        .login-text {{
            max-width: 420px;
            margin: 0 auto;
            color: {TEXT};
            line-height: 1.7;
            font-weight: 500;
        }}

        .login-bottom-bar {{
            position: absolute;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(135deg, {NAVY}, #070B3A);
            color: white;
            border-radius: 24px 24px 0 0;
            padding: 24px 30px;
            display: flex;
            justify-content: center;
            gap: 48px;
            text-align: left;
        }}

        .login-form-card {{
            background: white;
            border: 1px solid {BORDER};
            border-radius: 26px;
            padding: 56px 64px;
            box-shadow: 0 24px 60px rgba(13,20,100,0.13);
            max-width: 650px;
            width: 100%;
        }}

        .login-form-card h1 {{
            font-size: 38px;
            margin-bottom: 8px;
            color: {NAVY};
        }}

        .login-form-card p {{
            color: {MUTED};
            margin-bottom: 30px;
            font-size: 16px;
        }}

        .login-footer {{
            text-align: center;
            margin-top: 32px;
            color: {MUTED};
            font-size: 13px;
        }}

        .table-card {{
            background: {WHITE};
            border: 1px solid {BORDER};
            border-radius: 18px;
            padding: 16px;
            box-shadow: 0 14px 34px rgba(13,20,100,0.08);
            margin-top: 18px;
        }}

        [data-testid="stDataFrame"] {{
            border-radius: 15px;
            overflow: hidden;
        }}

        @media (max-width: 1000px) {{
            .login-container {{
                grid-template-columns: 1fr;
                gap: 20px;
            }}
            .login-left {{
                min-height: 430px;
            }}
            .login-bottom-bar {{
                position: relative;
                margin-top: 24px;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ==========================================================
# GOOGLE SHEETS
# ==========================================================
@st.cache_resource(ttl=3600)
def get_gspread_client():
    if "gcp_service_account" not in st.secrets:
        st.error("Configure o segredo [gcp_service_account] no Streamlit.")
        st.stop()

    info = dict(st.secrets["gcp_service_account"])

    if "private_key" in info:
        info["private_key"] = info["private_key"].replace("\\n", "\n")

    credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(credentials)


@st.cache_data(ttl=60, show_spinner=False)
def load_sheet_data():
    client = get_gspread_client()
    sh = client.open_by_key(SHEET_ID)
    ws = sh.worksheet(WORKSHEET_NAME)
    data = ws.get_all_records()
    df = pd.DataFrame(data)

    if df.empty:
        return df

    df.columns = [normalize_col(c) for c in df.columns]

    col_nome = find_col(df, ["Nome", "Cliente", "Nome completo"])
    col_telefone = find_col(df, ["Telefone", "Celular", "WhatsApp"])
    col_cpf = find_col(df, ["CPF"])
    col_email = find_col(df, ["E-mail", "Email"])
    col_data = find_col(df, ["Data Compra", "Data da Compra", "Data Venda", "Data da Venda"])
    col_mes = find_col(df, ["Mês", "Mes", "Mês da Compra", "Mês da Compra do Cliente"])
    col_unidade = find_col(df, ["Unidade", "Loja"])
    col_raca = find_col(df, ["Raça", "Raca"])
    col_sexo = find_col(df, ["Sexo"])
    col_cor = find_col(df, ["Cor"])
    col_vendedora = find_col(df, ["Vendedora", "Vendedor", "Consultora"])
    col_valor = find_col(df, ["Valor", "Valor Venda", "Valor da Venda", "Total"])
    col_status = find_col(df, ["Status", "Status Venda Pedigree", "Status Comercial"])
    col_pagamento = find_col(df, ["Pagamento", "Forma de Pagamento", "Forma pagamento"])

    df["_nome"] = df[col_nome].apply(clean_text) if col_nome else ""
    df["_telefone"] = df[col_telefone].apply(clean_phone) if col_telefone else ""
    df["_cpf"] = df[col_cpf].apply(clean_text) if col_cpf else ""
    df["_email"] = df[col_email].apply(clean_text) if col_email else ""
    df["_data"] = pd.to_datetime(df[col_data], dayfirst=True, errors="coerce") if col_data else pd.NaT
    df["_mes"] = df[col_mes].apply(clean_text) if col_mes else df["_data"].apply(month_from_date)
    df["_unidade"] = df[col_unidade].apply(clean_upper) if col_unidade else ""
    df["_raca"] = df[col_raca].apply(clean_upper) if col_raca else "NÃO INFORMADO"
    df["_sexo"] = df[col_sexo].apply(clean_upper) if col_sexo else "NÃO INFORMADO"
    df["_cor"] = df[col_cor].apply(clean_upper) if col_cor else "NÃO INFORMADO"
    df["_vendedora"] = df[col_vendedora].apply(clean_text) if col_vendedora else "Sem vendedora"
    df["_valor"] = df[col_valor].apply(parse_money) if col_valor else 0.0
    df["_status"] = df[col_status].apply(clean_text) if col_status else "Novo Lead"
    df["_pagamento"] = df[col_pagamento].apply(clean_text) if col_pagamento else "Não informado"

    if col_unidade:
        df = df[df["_unidade"].str.contains(UNIDADE_FIXA, na=False)].copy()

    return df


def append_to_sheet(row_dict):
    client = get_gspread_client()
    sh = client.open_by_key(SHEET_ID)
    ws = sh.worksheet(WORKSHEET_NAME)

    headers = [normalize_col(h) for h in ws.row_values(1)]
    new_row = [row_dict.get(h, "") for h in headers]
    ws.append_row(new_row, value_input_option="USER_ENTERED")


# ==========================================================
# LOGIN
# ==========================================================
def check_login(username, password):
    # Login padrão. Pode trocar no Streamlit Secrets:
    # [login]
    # username="skoobpet"
    # password="123456"
    default_user = "skoobpet"
    default_pass = "123456"

    user = st.secrets.get("login", {}).get("username", default_user) if hasattr(st, "secrets") else default_user
    pwd = st.secrets.get("login", {}).get("password", default_pass) if hasattr(st, "secrets") else default_pass

    return username == user and password == pwd


def login_page():
    logo = img_base64(LOGO_PATH)

    st.markdown(
        f"""
        <div class="login-container">
            <div class="login-left">
                <div class="paw-bg">🐾</div>
                {f'<img class="login-logo" src="data:image/png;base64,{logo}">' if logo else '<h1>SkoobPet</h1>'}
                <div class="login-title">Bem-vindo(a) de volta!</div>
                <div class="login-text">
                    Faça login para acessar o painel da SkoobPet<br>
                    e acompanhar os resultados da unidade<br>
                    <b>Campinas.</b>
                </div>
                <div class="pet-illustration">🐶🐱</div>

                <div class="login-bottom-bar">
                    <div>📍<br><b>Unidade selecionada</b><br>Campinas</div>
                    <div>🛡️<br><b>Seus dados protegidos</b><br>com segurança</div>
                </div>
            </div>

            <div class="login-form-card">
                <h1>Acessar conta</h1>
                <p>Informe suas credenciais para continuar</p>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        username = st.text_input("Usuário", placeholder="Digite seu usuário")
        password = st.text_input("Senha", placeholder="Digite sua senha", type="password")

        c1, c2 = st.columns([1, 1])
        with c1:
            lembrar = st.checkbox("Lembrar de mim")
        with c2:
            st.markdown(
                f"<div style='text-align:right; color:{MAGENTA}; font-weight:800; margin-top:8px;'>Esqueci minha senha</div>",
                unsafe_allow_html=True,
            )

        entrar = st.form_submit_button("Entrar", use_container_width=True)

    st.markdown(
        """
                <div class="login-footer">© 2026 SkoobPet. Todos os direitos reservados.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if entrar:
        if check_login(username, password):
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")


# ==========================================================
# COMPONENTES VISUAIS
# ==========================================================
def sidebar():
    logo = img_base64(LOGO_PATH)

    with st.sidebar:
        if logo:
            st.markdown(
                f"""
                <div class="sidebar-logo">
                    <img src="data:image/png;base64,{logo}">
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown("<h2 style='color:white;'>SkoobPet</h2>", unsafe_allow_html=True)

        page = st.radio(
            "Menu",
            ["🏠 Visão geral", "🧾 Formulário", "💵 Financeiro"],
            label_visibility="collapsed",
        )

        st.markdown(
            """
            <div class="sidebar-footer">
                <div style="font-size:15px; font-weight:800;">↪ Sair</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    return page.replace("🏠 ", "").replace("🧾 ", "").replace("💵 ", "")


def page_header(title, right=True):
    st.markdown(
        f"""
        <div class="page-header">
            <div class="title-wrap">
                <h1>{title}</h1>
                <div class="location">📍 Campinas</div>
            </div>
            <div class="top-actions">
                <div class="notice-bell">🔔</div>
                <div class="admin-pill"><span class="avatar">AD</span> Administrador ▾</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(icon, label, value, trend="↑ 15% vs mês anterior"):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-row">
                <div class="kpi-icon">{icon}</div>
                <div class="kpi-label">{label}</div>
            </div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-trend">{trend}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card_start(title, subtitle=None):
    sub = f'<div class="dash-card-subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div class="dash-card">
            <div class="dash-card-title">{title}</div>
            {sub}
        """,
        unsafe_allow_html=True,
    )


def card_end():
    st.markdown("</div>", unsafe_allow_html=True)


def month_options(df):
    meses = [m for m in df["_mes"].dropna().astype(str).unique() if m and m.lower() != "nan"]
    meses = sorted(meses)
    return ["Todos"] + meses


def apply_filters(df, mes, busca):
    filtered = df.copy()

    if mes != "Todos":
        filtered = filtered[filtered["_mes"].astype(str) == mes]

    if busca:
        b = busca.strip().lower()
        mask = (
            filtered["_nome"].astype(str).str.lower().str.contains(b, na=False)
            | filtered["_telefone"].astype(str).str.lower().str.contains(b, na=False)
            | filtered["_cpf"].astype(str).str.lower().str.contains(b, na=False)
            | filtered["_email"].astype(str).str.lower().str.contains(b, na=False)
            | filtered["_vendedora"].astype(str).str.lower().str.contains(b, na=False)
        )
        filtered = filtered[mask]

    return filtered


def filter_bar(df, key_prefix):
    with st.container():
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1.1, 1.7, 0.8])
        with c1:
            mes = st.selectbox("Período", month_options(df), key=f"{key_prefix}_mes")
        with c2:
            busca = st.text_input("Buscar", placeholder="Cliente, telefone, CPF, e-mail ou vendedora...", key=f"{key_prefix}_busca")
        with c3:
            st.write("")
            st.write("")
            if st.button("🔄 Atualizar", use_container_width=True, key=f"{key_prefix}_refresh"):
                st.cache_data.clear()
                st.rerun()

        st.markdown(
            f"""
            <div style="margin-top:8px;">
                <span class="chip">🐾 Unidade: Campinas</span>
                <span style="color:{MUTED}; font-size:13px;">Última atualização em tempo real pela planilha</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    return mes, busca


# ==========================================================
# GRÁFICOS
# ==========================================================
def line_chart(df, x_col, y_col, color, name):
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df[x_col],
            y=df[y_col],
            mode="lines+markers",
            line=dict(color=color, width=3),
            marker=dict(size=7, color=color),
            fill="tozeroy",
            fillcolor="rgba(197,0,82,0.12)" if color == MAGENTA else "rgba(13,20,100,0.08)",
            name=name,
        )
    )
    return fig_style(fig)


def bar_chart(df, x_col, y_col, horizontal=False, colors=None, height=330):
    fig = go.Figure()
    color_list = colors if colors else [MAGENTA] * len(df)
    if horizontal:
        fig.add_trace(
            go.Bar(
                x=df[y_col],
                y=df[x_col],
                orientation="h",
                marker=dict(color=color_list),
                text=df[y_col],
                textposition="outside",
            )
        )
        fig.update_layout(yaxis=dict(autorange="reversed"))
    else:
        fig.add_trace(
            go.Bar(
                x=df[x_col],
                y=df[y_col],
                marker=dict(color=color_list),
                text=df[y_col],
                textposition="outside",
            )
        )
    return fig_style(fig, height=height)


def donut_chart(labels, values):
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.62,
                marker=dict(colors=[MAGENTA, NAVY, "#4B2991", "#F08BC0"]),
                textinfo="percent",
            )
        ]
    )
    fig.update_layout(
        height=330,
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
        font=dict(family="Inter, Arial", color=TEXT),
        legend=dict(x=0.72, y=0.5),
        annotations=[
            dict(
                text="100%",
                x=0.5,
                y=0.5,
                font_size=20,
                font_color=NAVY,
                showarrow=False,
            )
        ],
    )
    return fig


# ==========================================================
# VISÃO GERAL
# ==========================================================
def page_overview(df):
    page_header("Visão geral")
    mes, busca = filter_bar(df, "overview")
    filtered = apply_filters(df, mes, busca)

    hoje = pd.Timestamp(date.today())
    mes_atual = len(filtered)
    vendas = int(filtered["_status"].astype(str).str.lower().str.contains("fechado|vend|pago|concluído|concluido", na=False).sum())
    faturamento = filtered["_valor"].sum()
    ticket = faturamento / max(vendas, 1)
    novos = int(filtered["_status"].astype(str).str.lower().str.contains("novo", na=False).sum())

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("☎️", "Contatos no mês", mes_atual)
    with c2:
        kpi_card("🛒", "Vendas no mês", vendas, "↑ 22% vs mês anterior")
    with c3:
        kpi_card("🎟️", "Ticket médio", br_money(ticket), "↑ 8% vs mês anterior")
    with c4:
        kpi_card("💵", "Faturamento no mês", br_money(faturamento), "↑ 18% vs mês anterior")
    with c5:
        kpi_card("🐾", "Novos clientes", novos, "↑ 9% vs mês anterior")

    st.write("")

    if filtered.empty:
        st.info("Sem dados para os filtros selecionados.")
        return

    by_day = (
        filtered.dropna(subset=["_data"])
        .groupby(filtered["_data"].dt.strftime("%d/%m"))
        .size()
        .reset_index(name="Quantidade")
        .rename(columns={"_data": "Dia"})
    )
    if by_day.empty:
        by_day = pd.DataFrame({"Dia": ["Sem data"], "Quantidade": [0]})

    vendas_day = (
        filtered[filtered["_status"].astype(str).str.lower().str.contains("fechado|vend|pago|concluído|concluido", na=False)]
        .dropna(subset=["_data"])
        .groupby(filtered["_data"].dt.strftime("%d/%m"))
        .size()
        .reset_index(name="Quantidade")
        .rename(columns={"_data": "Dia"})
    )
    if vendas_day.empty:
        vendas_day = by_day.copy()

    r1c1, r1c2, r1c3 = st.columns([1, 1, 1.12])
    with r1c1:
        card_start("Contatos por dia")
        st.plotly_chart(line_chart(by_day, "Dia", "Quantidade", MAGENTA, "Contatos"), use_container_width=True)
        card_end()

    with r1c2:
        card_start("Vendas por dia")
        st.plotly_chart(line_chart(vendas_day, "Dia", "Quantidade", NAVY_2, "Vendas"), use_container_width=True)
        card_end()

    with r1c3:
        card_start("Vendas por unidade")
        st.plotly_chart(donut_chart(["Campinas", "Indaiatuba", "Piracicaba"], [100, 0, 0]), use_container_width=True)
        card_end()

    r2c1, r2c2, r2c3 = st.columns([1, 1.25, 0.9])
    with r2c1:
        card_start("Raças mais vendidas (mês)")
        tmp = filtered["_raca"].replace("", "NÃO INFORMADO").value_counts().head(6).reset_index()
        tmp.columns = ["Raça", "Quantidade"]
        st.plotly_chart(bar_chart(tmp, "Raça", "Quantidade", horizontal=True, height=300), use_container_width=True)
        card_end()

    with r2c2:
        card_start("Vendas por vendedora (mês)")
        tmp = filtered["_vendedora"].replace("", "Sem vendedora").value_counts().head(8).reset_index()
        tmp.columns = ["Vendedora", "Quantidade"]
        colors = [MAGENTA if i % 2 == 0 else NAVY for i in range(len(tmp))]
        st.plotly_chart(bar_chart(tmp, "Vendedora", "Quantidade", colors=colors, height=300), use_container_width=True)
        card_end()

    with r2c3:
        card_start("Resumo por status")
        status = filtered["_status"].replace("", "Sem status").value_counts().reset_index()
        status.columns = ["Status", "Quantidade"]
        total = max(status["Quantidade"].sum(), 1)

        color_status = [NAVY, GREEN, "#D99B00", "#F97316", MAGENTA, "#5867DD"]
        rows = ""
        for i, row in status.head(7).iterrows():
            pct = int((row["Quantidade"] / total) * 100)
            color = color_status[i % len(color_status)]
            rows += f"""
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(13,20,100,0.08); padding:11px 0;">
                <div><span class="status-dot" style="background:{color};"></span>{row["Status"]}</div>
                <div style="font-weight:900; color:{NAVY};">{row["Quantidade"]} ({pct}%)</div>
            </div>
            """
        st.markdown(rows, unsafe_allow_html=True)
        card_end()

    st.markdown(
        f"""
        <div class="filter-card" style="display:flex; align-items:center; justify-content:space-between;">
            <div>
                <span class="chip">🐾 Filtros aplicados: Unidade Campinas</span>
                <span style="color:{NAVY}; font-weight:800;">Limpar filtros</span>
            </div>
            <div style="color:{MUTED}; font-weight:700;">Última atualização: automática</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================================
# FORMULÁRIO
# ==========================================================
def page_form(df):
    page_header("Formulário")

    st.markdown(
        """
        <div class="stepper">
            <div class="step active"><span class="step-number">1</span> Dados do cliente</div>
            <div class="step"><span class="step-number">2</span> Informações</div>
            <div class="step"><span class="step-number">3</span> Produtos/Serviços</div>
            <div class="step"><span class="step-number">4</span> Conclusão</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([2.2, 0.9])
    with left:
        st.markdown('<div class="form-shell">', unsafe_allow_html=True)
        st.markdown(f"<h3 style='font-size:19px; margin-top:0;'>Dados do cliente</h3>", unsafe_allow_html=True)

        with st.form("cadastro_skoobpet", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                nome = st.text_input("Nome completo", placeholder="Digite o nome do cliente")
                email = st.text_input("E-mail", placeholder="email@exemplo.com")
                cpf = st.text_input("CPF", placeholder="000.000.000-00")
                data_compra = st.date_input("Data da compra", value=date.today(), format="DD/MM/YYYY")
            with c2:
                telefone = st.text_input("Telefone", placeholder="(19) 99999-9999")
                origem = st.selectbox("Como conheceu a SkoobPet?", ["Selecione", "Instagram", "WhatsApp", "Indicação", "Loja", "Google"])
                unidade = st.text_input("Unidade", value="Campinas", disabled=True)
                vendedora = st.text_input("Vendedora", placeholder="Nome da vendedora")

            st.markdown(f"<h3 style='font-size:19px;'>Dados do pet / serviço</h3>", unsafe_allow_html=True)
            p1, p2, p3 = st.columns(3)
            with p1:
                raca = st.text_input("Raça")
                sexo = st.selectbox("Sexo", ["", "FÊMEA", "MACHO"])
            with p2:
                cor = st.text_input("Cor")
                status = st.selectbox("Status", ["Novo Lead", "Conversando", "Sem interesse", "Não responde", "Fechado", "Proposta", "Reunião"])
            with p3:
                pagamento = st.selectbox("Forma de pagamento", ["Não informado", "Pix", "Cartão", "Dinheiro", "Boleto"])
                valor = st.number_input("Valor", min_value=0.0, step=10.0, format="%.2f")

            observacoes = st.text_area("Observações", placeholder="Digite observações adicionais...")

            b1, b2, b3 = st.columns([1, 1, 1])
            with b1:
                cancelar = st.form_submit_button("Cancelar", use_container_width=True)
            with b3:
                salvar = st.form_submit_button("Próximo →", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

        if salvar:
            data_str = data_compra.strftime("%d/%m/%Y")
            mes_str = data_compra.strftime("%m/%Y")
            valor_str = br_money(valor).replace("R$ ", "")

            row = {
                "Nome": nome,
                "Telefone": telefone,
                "CPF": cpf,
                "E-mail": email,
                "Data Compra": data_str,
                "Mês": mes_str,
                "Raça": raca,
                "Sexo": sexo,
                "Cor": cor,
                "Unidade": UNIDADE_FIXA,
                "Vendedora": vendedora,
                "Valor": valor_str,
                "Status": status,
                "Forma de Pagamento": pagamento,
                "Observações": observacoes,
                "Origem": origem,
            }

            try:
                append_to_sheet(row)
                st.cache_data.clear()
                st.success("Cadastro salvo na planilha com sucesso!")
            except Exception as e:
                st.error(f"Não foi possível salvar na planilha: {e}")

    with right:
        st.markdown(
            f"""
            <div class="summary-box">
                <h3 style="font-size:19px; margin-top:0;">Resumo do atendimento</h3>
                <div style="color:{MUTED}; font-weight:700; margin-top:18px;">Cliente</div>
                <div style="font-weight:900; color:{NAVY}; margin-bottom:18px;">-</div>
                <div style="color:{MUTED}; font-weight:700;">Produtos/Serviços</div>
                <div style="font-weight:900; color:{TEXT}; margin-bottom:18px;">0 itens</div>
                <hr style="border:none; border-top:1px solid rgba(13,20,100,0.10);">
                <div style="color:{MUTED}; font-weight:700;">Total</div>
                <div class="summary-total">R$ 0,00</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="table-card">', unsafe_allow_html=True)
    st.markdown(f"<h3 style='font-size:19px; margin-top:0;'>Histórico de atendimentos</h3>", unsafe_allow_html=True)

    mes, busca = filter_bar(df, "form_hist")
    filtered = apply_filters(df, mes, busca)

    show_cols = []
    for c in ["Nome", "Telefone", "CPF", "E-mail", "Data Compra", "Mês", "Raça", "Sexo", "Cor", "Unidade", "Vendedora", "Valor", "Status"]:
        if c in filtered.columns:
            show_cols.append(c)

    if show_cols:
        st.dataframe(filtered[show_cols].tail(20), use_container_width=True, hide_index=True)
    else:
        st.dataframe(filtered.drop(columns=[c for c in filtered.columns if c.startswith("_")], errors="ignore").tail(20), use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ==========================================================
# FINANCEIRO
# ==========================================================
def page_finance(df):
    page_header("Financeiro")
    mes, busca = filter_bar(df, "finance")
    filtered = apply_filters(df, mes, busca)

    faturamento = filtered["_valor"].sum()
    recebido = filtered[filtered["_status"].astype(str).str.lower().str.contains("pago|fechado|concluído|concluido|vend", na=False)]["_valor"].sum()
    pendente = max(faturamento - recebido, 0)
    vendas = len(filtered)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("💵", "Faturamento bruto", br_money(faturamento), "↑ 18% vs período anterior")
    with c2:
        kpi_card("💳", "Recebido", br_money(recebido), "↑ 20% vs período anterior")
    with c3:
        kpi_card("📌", "Pendente", br_money(pendente), "↓ 5% vs período anterior")
    with c4:
        kpi_card("🛒", "Nº de vendas", vendas, "↑ 22% vs período anterior")

    if filtered.empty:
        st.info("Sem dados para os filtros selecionados.")
        return

    by_day_value = (
        filtered.dropna(subset=["_data"])
        .groupby(filtered["_data"].dt.strftime("%d/%m"))["_valor"]
        .sum()
        .reset_index()
        .rename(columns={"_data": "Dia", "_valor": "Valor"})
    )
    if by_day_value.empty:
        by_day_value = pd.DataFrame({"Dia": ["Sem data"], "Valor": [0.0]})

    f1, f2 = st.columns([2.1, 1])
    with f1:
        card_start("Faturamento ao longo do tempo")
        st.plotly_chart(line_chart(by_day_value, "Dia", "Valor", MAGENTA, "Faturamento"), use_container_width=True)
        card_end()

    with f2:
        card_start("Forma de pagamento")
        pay = filtered["_pagamento"].replace("", "Não informado").value_counts().reset_index()
        pay.columns = ["Pagamento", "Quantidade"]
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=pay["Pagamento"],
                    values=pay["Quantidade"],
                    hole=0.58,
                    marker=dict(colors=[MAGENTA, NAVY, "#5B2AA2", "#F08BC0"]),
                )
            ]
        )
        fig.update_layout(
            height=330,
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=10, b=10),
            font=dict(family="Inter, Arial", color=TEXT),
            legend=dict(x=0.72, y=0.5),
        )
        st.plotly_chart(fig, use_container_width=True)
        card_end()

    st.markdown('<div class="table-card">', unsafe_allow_html=True)
    st.markdown(f"<h3 style='font-size:19px; margin-top:0;'>Últimas vendas</h3>", unsafe_allow_html=True)

    show_cols = []
    for c in ["Data Compra", "Nome", "Raça", "Vendedora", "Forma de Pagamento", "Valor", "Status"]:
        if c in filtered.columns:
            show_cols.append(c)

    if show_cols:
        st.dataframe(filtered[show_cols].tail(15), use_container_width=True, hide_index=True)
    else:
        st.dataframe(filtered.drop(columns=[c for c in filtered.columns if c.startswith("_")], errors="ignore").tail(15), use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)


# ==========================================================
# MAIN
# ==========================================================
def main():
    app_css()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_page()
        return

    page = sidebar()

    with st.spinner("Carregando dados da planilha..."):
        df = load_sheet_data()

    if df.empty:
        st.warning("A planilha está vazia ou não foi possível carregar os dados.")
        return

    if page == "Visão geral":
        page_overview(df)
    elif page == "Formulário":
        page_form(df)
    elif page == "Financeiro":
        page_finance(df)


if __name__ == "__main__":
    main()
