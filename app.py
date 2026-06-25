import base64
import re
from datetime import datetime, date
from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    import gspread
    from google.oauth2.service_account import Credentials
except Exception:
    gspread = None
    Credentials = None

# =========================================================
# DASHBOARD SKOOB PET - CAMPINAS
# Desenvolvido para GitHub + Streamlit Cloud
# =========================================================

st.set_page_config(
    page_title="SkoobPet | Dashboard Campinas",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- CONFIGURAÇÕES ----------------
APP_TITLE = "SkoobPet"
UNIDADE_DASHBOARD = "Campinas"
LOGO_PATH = Path("skoobpet.png")

# Usuário/senha padrão. No Streamlit Cloud, você pode trocar em Secrets.
DEFAULT_USER = "administrador"
DEFAULT_PASSWORD = "skoobpet123"

# Nome/URL da planilha. No Streamlit Cloud, configure SHEET_URL ou SHEET_ID em Secrets.
DEFAULT_SHEET_NAME = "Controle Pos e Pedigree 2026"
DEFAULT_WORKSHEET = "Clear"

SKOOB_NAVY = "#16135f"
SKOOB_NAVY_2 = "#0b0f45"
SKOOB_PINK = "#d4006a"
SKOOB_PINK_2 = "#f0087f"
SKOOB_BG = "#fff6fb"
SKOOB_SOFT = "#f8edf6"
SKOOB_TEXT = "#090044"
SKOOB_MUTED = "#6b6685"
GREEN = "#16a34a"
RED = "#dc2626"
ORANGE = "#f59e0b"

STATUS_OPTIONS = ["Novo Lead", "Conversando", "Sem interesse", "Aguardando", "Fechado"]
PAYMENT_OPTIONS = ["Dinheiro", "Cartão", "PIX", "Boleto", "Transferência"]
SERVICE_OPTIONS = [
    "Banho e Tosa",
    "Ração Premium",
    "Vacina V8",
    "Vacina V10",
    "Consulta Veterinária",
    "Pedigree",
    "Microchip",
    "Acessório",
]

# ---------------- CSS ----------------
def img_to_base64(path: Path) -> str:
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode("utf-8")


def inject_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        * {{ font-family: 'Inter', sans-serif; }}

        .stApp {{
            background: radial-gradient(circle at top left, #fff3fb 0%, #fff9fd 34%, #ffffff 100%);
            color: {SKOOB_TEXT};
        }}

        #MainMenu, footer, header {{ visibility: hidden; }}
        .block-container {{ padding-top: 1.1rem; padding-bottom: 2rem; max-width: 1500px; }}

        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {SKOOB_NAVY} 0%, {SKOOB_NAVY_2} 100%);
            border-right: 0;
            min-width: 250px !important;
            width: 250px !important;
        }}
        section[data-testid="stSidebar"] * {{ color: #fff; }}
        section[data-testid="stSidebar"] .stRadio label {{ color: #fff !important; }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label {{
            padding: 13px 14px;
            border-radius: 12px;
            margin-bottom: 8px;
            transition: .2s ease;
            color: #fff !important;
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
            background: rgba(255,255,255,.11);
        }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label[data-baseweb="radio"] span:first-child {{ display:none; }}
        section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
            background: linear-gradient(90deg, {SKOOB_PINK} 0%, {SKOOB_PINK_2} 100%);
            box-shadow: 0 12px 25px rgba(212,0,106,.28);
        }}

        .sidebar-logo {{ text-align:center; margin: 8px 0 18px; }}
        .sidebar-logo img {{ width: 145px; max-width: 90%; }}
        .sidebar-user {{
            position: fixed;
            bottom: 18px;
            left: 28px;
            font-size: 13px;
            opacity: .95;
        }}

        .page-title {{
            font-size: 30px;
            font-weight: 850;
            color: {SKOOB_TEXT};
            margin-bottom: 0;
            letter-spacing: -0.8px;
        }}
        .page-subtitle {{
            color: {SKOOB_PINK};
            font-size: 14px;
            font-weight: 700;
            margin-top: -2px;
            margin-bottom: 18px;
        }}

        .kpi-card {{
            background: rgba(255,255,255,.92);
            border: 1px solid #f0dce9;
            border-radius: 16px;
            padding: 20px 20px 17px;
            box-shadow: 0 10px 28px rgba(22,19,95,.08);
            min-height: 122px;
        }}
        .kpi-icon {{ color: {SKOOB_PINK}; font-size: 20px; margin-bottom: 8px; }}
        .kpi-title {{ color: {SKOOB_TEXT}; font-size: 13px; font-weight: 700; margin-bottom: 8px; }}
        .kpi-value {{ color: {SKOOB_TEXT}; font-size: 29px; font-weight: 850; line-height: 1; }}
        .kpi-delta {{ color: {GREEN}; font-size: 12px; margin-top: 10px; font-weight: 700; }}
        .kpi-delta.red {{ color: {RED}; }}

        .chart-card, .form-card, .table-card {{
            background: rgba(255,255,255,.94);
            border: 1px solid #f0dce9;
            border-radius: 16px;
            padding: 18px;
            box-shadow: 0 10px 28px rgba(22,19,95,.075);
            height: 100%;
        }}
        .chart-title {{ font-weight: 800; color: {SKOOB_TEXT}; margin-bottom: 10px; }}

        .login-wrap {{
            min-height: 91vh;
            display: grid;
            grid-template-columns: 1fr 410px;
            align-items: center;
            gap: 70px;
            padding: 20px 8vw;
            position: relative;
            overflow: hidden;
        }}
        .login-wrap:before {{
            content: "";
            position: absolute;
            left: -120px;
            bottom: -90px;
            width: 460px;
            height: 460px;
            background: radial-gradient(circle, rgba(212,0,106,.12) 0 14%, transparent 15% 100%);
            background-size: 88px 88px;
            opacity: .75;
        }}
        .login-left {{ text-align: center; z-index: 1; }}
        .login-left img {{ width: 230px; margin-bottom: 18px; }}
        .login-left h2 {{ color: {SKOOB_PINK}; font-size: 20px; margin-bottom: 16px; }}
        .login-left p {{ color: {SKOOB_TEXT}; font-weight: 500; line-height: 1.55; max-width: 360px; margin: auto; }}
        .login-card {{
            background: rgba(255,255,255,.88);
            backdrop-filter: blur(12px);
            border: 1px solid #eadbe6;
            border-radius: 18px;
            padding: 34px;
            box-shadow: 0 24px 60px rgba(22,19,95,.14);
            z-index: 1;
        }}
        .login-card h1 {{ font-size: 23px; color: {SKOOB_TEXT}; margin-bottom: 25px; }}
        .stButton>button {{
            background: linear-gradient(90deg, {SKOOB_NAVY} 0%, {SKOOB_PINK} 100%);
            color: white;
            border: none;
            border-radius: 10px;
            height: 46px;
            font-weight: 800;
            box-shadow: 0 12px 24px rgba(212,0,106,.20);
        }}
        .stButton>button:hover {{ border: none; transform: translateY(-1px); color: #fff; }}
        .stTextInput input, .stNumberInput input, .stDateInput input, textarea, .stSelectbox div[data-baseweb="select"] {{
            border-radius: 10px !important;
        }}

        .step-box {{
            display:flex; align-items:center; justify-content:space-between;
            background:#fff; border:1px solid #f0dce9; border-radius:14px; padding:16px 22px;
            margin-bottom:18px; box-shadow:0 8px 24px rgba(22,19,95,.07);
        }}
        .step {{ display:flex; align-items:center; gap:10px; color:{SKOOB_MUTED}; font-weight:700; font-size:13px; }}
        .step-num {{ width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#eef0f5;color:{SKOOB_MUTED};font-size:12px; }}
        .step.active .step-num {{ background:{SKOOB_PINK}; color:#fff; }}
        .step.active {{ color:{SKOOB_PINK}; }}
        .divider {{ height:1px;background:#ece4ec;flex:1;margin:0 14px; }}

        .status-pago {{ color: {GREEN}; font-weight: 800; }}
        .status-pendente {{ color: {RED}; font-weight: 800; }}
        .small-muted {{ color:{SKOOB_MUTED}; font-size:12px; }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# ---------------- HELPERS ----------------
def get_secret(key, default=None):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


def normalize_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def find_col(df, candidates):
    cols = {str(c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        cand_l = cand.lower()
        for key, original in cols.items():
            if key == cand_l or cand_l in key:
                return original
    return None


def parse_money(value):
    if pd.isna(value) or str(value).strip() == "":
        return 0.0
    text = str(value).replace("R$", "").replace(" ", "").strip()
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except Exception:
        nums = re.findall(r"\d+\.?\d*", text)
        return float(nums[0]) if nums else 0.0


def money_br(value):
    try:
        value = float(value)
    except Exception:
        value = 0.0
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def phone_clean(value):
    return re.sub(r"\D", "", str(value or ""))


def prepare_dataframe(df_raw: pd.DataFrame) -> pd.DataFrame:
    df = df_raw.copy()
    df = df.dropna(how="all")
    df.columns = [str(c).strip() for c in df.columns]

    col_unidade = find_col(df, ["Unidade", "Loja", "Cidade"])
    if col_unidade:
        df = df[df[col_unidade].astype(str).str.contains(UNIDADE_DASHBOARD, case=False, na=False)]

    col_data = find_col(df, ["Data Compra", "Data da Compra", "Data da Venda", "Data Venda", "Data"])
    if col_data:
        df["__data"] = pd.to_datetime(df[col_data], errors="coerce", dayfirst=True)
    else:
        df["__data"] = pd.NaT

    col_valor = find_col(df, ["Valor", "Total", "Faturamento", "Preço", "Preco"])
    df["__valor"] = df[col_valor].apply(parse_money) if col_valor else 0.0

    col_status = find_col(df, ["Status", "Status Venda", "Status Atendimento"])
    df["__status"] = df[col_status].fillna("Novo Lead").astype(str) if col_status else "Novo Lead"

    col_raca = find_col(df, ["Raça", "Raca"])
    df["__raca"] = df[col_raca].fillna("Não informado").astype(str) if col_raca else "Não informado"

    col_vendedora = find_col(df, ["Vendedora", "Vendedor", "Responsável", "Responsavel"])
    df["__vendedora"] = df[col_vendedora].fillna("Não informado").astype(str) if col_vendedora else "Não informado"

    col_pag = find_col(df, ["Forma de Pagamento", "Pagamento", "Forma pagamento"])
    df["__pagamento"] = df[col_pag].fillna("Não informado").astype(str) if col_pag else "Não informado"

    col_prod = find_col(df, ["Produto", "Produto/Serviço", "Servico", "Serviço", "Produtos/Serviços"])
    df["__produto"] = df[col_prod].fillna("Não informado").astype(str) if col_prod else "Não informado"

    col_nome = find_col(df, ["Nome", "Cliente", "Tutor"])
    df["__nome"] = df[col_nome].fillna("Não informado").astype(str) if col_nome else "Não informado"

    col_tel = find_col(df, ["Telefone", "Celular", "Whatsapp", "WhatsApp"])
    df["__telefone"] = df[col_tel].fillna("").astype(str) if col_tel else ""

    return df.reset_index(drop=True)


@st.cache_data(ttl=300, show_spinner=False)
def load_data_cached():
    return load_data()


def load_data():
    if gspread is None:
        st.error("As bibliotecas do Google Sheets não foram carregadas. Confira o requirements.txt.")
        return pd.DataFrame()

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    creds_dict = None
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
        elif "GOOGLE_SERVICE_ACCOUNT" in st.secrets:
            import json
            creds_dict = json.loads(st.secrets["GOOGLE_SERVICE_ACCOUNT"])
    except Exception:
        creds_dict = None

    if not creds_dict:
        st.warning("Configure as credenciais do Google Sheets em Settings > Secrets no Streamlit Cloud.")
        return pd.DataFrame()

    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(credentials)

    sheet_url = get_secret("SHEET_URL", "")
    sheet_id = get_secret("SHEET_ID", "")
    sheet_name = get_secret("SHEET_NAME", DEFAULT_SHEET_NAME)
    worksheet_name = get_secret("WORKSHEET_NAME", DEFAULT_WORKSHEET)

    if sheet_url:
        spreadsheet = client.open_by_url(sheet_url)
    elif sheet_id:
        spreadsheet = client.open_by_key(sheet_id)
    else:
        spreadsheet = client.open(sheet_name)

    worksheet = spreadsheet.worksheet(worksheet_name)
    values = worksheet.get_all_records()
    return prepare_dataframe(pd.DataFrame(values))


def append_to_sheet(row_dict):
    if gspread is None:
        st.error("Bibliotecas Google Sheets ausentes.")
        return False
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds_dict = dict(st.secrets["gcp_service_account"])
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(credentials)
        sheet_url = get_secret("SHEET_URL", "")
        sheet_id = get_secret("SHEET_ID", "")
        sheet_name = get_secret("SHEET_NAME", DEFAULT_SHEET_NAME)
        worksheet_name = get_secret("WORKSHEET_NAME", DEFAULT_WORKSHEET)
        spreadsheet = client.open_by_url(sheet_url) if sheet_url else client.open_by_key(sheet_id) if sheet_id else client.open(sheet_name)
        worksheet = spreadsheet.worksheet(worksheet_name)
        headers = worksheet.row_values(1)
        row = [row_dict.get(h, "") for h in headers]
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar na planilha: {e}")
        return False


def filter_period(df, start, end):
    if df.empty or "__data" not in df:
        return df
    if pd.isna(df["__data"]).all():
        return df
    return df[(df["__data"].dt.date >= start) & (df["__data"].dt.date <= end)]


def kpi_card(title, value, delta="↑ 0% vs período anterior", icon="🐾", negative=False):
    cls = "kpi-delta red" if negative else "kpi-delta"
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="{cls}">{delta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(title):
    st.markdown(f"<div class='page-title'>{title}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='page-subtitle'>📍 {UNIDADE_DASHBOARD}</div>", unsafe_allow_html=True)


def empty_fig(message="Sem dados no período"):
    fig = go.Figure()
    fig.add_annotation(text=message, x=0.5, y=0.5, showarrow=False, font=dict(size=16, color=SKOOB_MUTED))
    fig.update_layout(height=260, margin=dict(l=20, r=20, t=20, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig


def style_fig(fig, height=280):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=15, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=SKOOB_TEXT, family="Inter"),
        legend=dict(orientation="v", yanchor="middle", y=.5, xanchor="left", x=1.02),
    )
    fig.update_xaxes(gridcolor="#f1e5ee", zeroline=False)
    fig.update_yaxes(gridcolor="#f1e5ee", zeroline=False)
    return fig

# ---------------- LOGIN ----------------
def render_login():
    logo_b64 = img_to_base64(LOGO_PATH)
    logo_html = f"<img src='data:image/png;base64,{logo_b64}' />" if logo_b64 else "<h1>SkoobPet</h1>"
    st.markdown(
        f"""
        <div class="login-wrap">
            <div class="login-left">
                {logo_html}
                <h2>Bem-vindo(a) de volta!</h2>
                <p>Faça login para acessar o painel da SkoobPet e acompanhar os resultados da unidade Campinas.</p>
            </div>
            <div class="login-card">
                <h1>Acessar conta</h1>
        """,
        unsafe_allow_html=True,
    )
    with st.form("login_form"):
        username = st.text_input("Usuário", placeholder="Digite seu usuário")
        password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        remember = st.checkbox("Lembrar de mim")
        submitted = st.form_submit_button("Entrar", use_container_width=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

    valid_user = get_secret("LOGIN_USER", DEFAULT_USER)
    valid_pass = get_secret("LOGIN_PASSWORD", DEFAULT_PASSWORD)
    if submitted:
        if username == valid_user and password == valid_pass:
            st.session_state["logged"] = True
            st.session_state["user"] = username
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

# ---------------- SIDEBAR ----------------
def render_sidebar():
    logo_b64 = img_to_base64(LOGO_PATH)
    if logo_b64:
        st.sidebar.markdown(f"<div class='sidebar-logo'><img src='data:image/png;base64,{logo_b64}' /></div>", unsafe_allow_html=True)
    else:
        st.sidebar.markdown("<h2 style='text-align:center'>SkoobPet</h2>", unsafe_allow_html=True)
    page = st.sidebar.radio(
        "",
        ["📊  Visão geral", "📝  Formulário", "💰  Financeiro"],
        label_visibility="collapsed",
    )
    st.sidebar.markdown("<div class='sidebar-user'>↪ Sair</div>", unsafe_allow_html=True)
    if st.sidebar.button("Sair da conta", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    return page

# ---------------- VISÃO GERAL ----------------
def render_overview(df):
    top1, top2 = st.columns([6, 2])
    with top1:
        page_header("Visão geral")
    with top2:
        if not df.empty and not pd.isna(df["__data"]).all():
            min_d = df["__data"].min().date()
            max_d = df["__data"].max().date()
        else:
            today = date.today(); min_d = date(today.year, today.month, 1); max_d = today
        period = st.date_input("Período", value=(min_d, max_d), label_visibility="collapsed")
    if isinstance(period, tuple) and len(period) == 2:
        start, end = period
    else:
        start, end = min_d, max_d
    dff = filter_period(df, start, end)

    total_contatos = len(dff)
    vendas = int((dff["__status"].astype(str).str.contains("fechado|pago|concluído|concluido", case=False, na=False)).sum()) if not dff.empty else 0
    faturamento = dff["__valor"].sum() if not dff.empty else 0
    ticket = faturamento / vendas if vendas else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Contatos no mês", total_contatos, "↑ Campinas", "🐾")
    with c2: kpi_card("Vendas no mês", vendas, "↑ filtrado por Campinas", "🛍️")
    with c3: kpi_card("Ticket médio", money_br(ticket), "↑ calculado pelas vendas", "💎")
    with c4: kpi_card("Faturamento no mês", money_br(faturamento), "↑ somente Campinas", "💰")

    st.write("")
    g1, g2, g3 = st.columns([1.1, 1.1, .9])
    with g1:
        st.markdown("<div class='chart-card'><div class='chart-title'>Contatos por dia</div>", unsafe_allow_html=True)
        if dff.empty or pd.isna(dff["__data"]).all():
            st.plotly_chart(empty_fig(), use_container_width=True)
        else:
            daily = dff.groupby(dff["__data"].dt.date).size().reset_index(name="Contatos")
            daily.columns = ["Data", "Contatos"]
            fig = px.line(daily, x="Data", y="Contatos", markers=True)
            fig.update_traces(line=dict(color=SKOOB_PINK, width=3), marker=dict(size=7))
            st.plotly_chart(style_fig(fig), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with g2:
        st.markdown("<div class='chart-card'><div class='chart-title'>Vendas por dia</div>", unsafe_allow_html=True)
        if dff.empty or pd.isna(dff["__data"]).all():
            st.plotly_chart(empty_fig(), use_container_width=True)
        else:
            sold = dff[dff["__status"].astype(str).str.contains("fechado|pago|concluído|concluido", case=False, na=False)]
            daily = sold.groupby(sold["__data"].dt.date).size().reset_index(name="Vendas") if not sold.empty else pd.DataFrame(columns=["Data", "Vendas"])
            fig = px.line(daily, x="Data", y="Vendas", markers=True) if not daily.empty else empty_fig()
            if not daily.empty: fig.update_traces(line=dict(color=SKOOB_NAVY, width=3), marker=dict(size=7))
            st.plotly_chart(style_fig(fig), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with g3:
        st.markdown("<div class='chart-card'><div class='chart-title'>Vendas por unidade</div>", unsafe_allow_html=True)
        fig = go.Figure(data=[go.Pie(labels=[UNIDADE_DASHBOARD], values=[100], hole=.62, marker=dict(colors=[SKOOB_PINK]))])
        fig.update_traces(textinfo="percent", textfont=dict(color="white", size=16))
        fig.update_layout(annotations=[dict(text="100%", x=.5, y=.5, font_size=18, showarrow=False, font_color=SKOOB_TEXT)])
        st.plotly_chart(style_fig(fig), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    b1, b2, b3 = st.columns([1.1, 1.2, .9])
    with b1:
        st.markdown("<div class='chart-card'><div class='chart-title'>Raças mais vendidas (mês)</div>", unsafe_allow_html=True)
        if dff.empty:
            st.plotly_chart(empty_fig(), use_container_width=True)
        else:
            raca = dff["__raca"].value_counts().head(6).reset_index()
            raca.columns = ["Raça", "Qtd"]
            fig = px.bar(raca.sort_values("Qtd"), x="Qtd", y="Raça", orientation="h", text="Qtd")
            fig.update_traces(marker_color=SKOOB_PINK, textposition="outside")
            st.plotly_chart(style_fig(fig, 255), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with b2:
        st.markdown("<div class='chart-card'><div class='chart-title'>Vendas por vendedora (mês)</div>", unsafe_allow_html=True)
        if dff.empty:
            st.plotly_chart(empty_fig(), use_container_width=True)
        else:
            vend = dff["__vendedora"].value_counts().head(7).reset_index()
            vend.columns = ["Vendedora", "Qtd"]
            fig = px.bar(vend, x="Vendedora", y="Qtd", text="Qtd")
            fig.update_traces(marker_color=SKOOB_PINK, textposition="outside")
            st.plotly_chart(style_fig(fig, 255), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with b3:
        st.markdown("<div class='chart-card'><div class='chart-title'>Resumo por status</div>", unsafe_allow_html=True)
        if dff.empty:
            st.plotly_chart(empty_fig(), use_container_width=True)
        else:
            status = dff["__status"].replace("", "Novo Lead").value_counts().reset_index()
            status.columns = ["Status", "Qtd"]
            fig = px.pie(status, names="Status", values="Qtd", hole=.45, color_discrete_sequence=[SKOOB_NAVY, "#00a887", ORANGE, "#ffbf00", SKOOB_PINK])
            st.plotly_chart(style_fig(fig, 255), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ---------------- FORMULÁRIO ----------------
def render_form(df):
    page_header("Formulário")
    st.markdown(
        """
        <div class='step-box'>
            <div class='step active'><div class='step-num'>1</div>Dados do cliente</div><div class='divider'></div>
            <div class='step'><div class='step-num'>2</div>Informações</div><div class='divider'></div>
            <div class='step'><div class='step-num'>3</div>Produtos/Serviços</div><div class='divider'></div>
            <div class='step'><div class='step-num'>4</div>Conclusão</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([2.2, .8])
    with left:
        st.markdown("<div class='form-card'><div class='chart-title'>Dados do cliente</div>", unsafe_allow_html=True)
        with st.form("new_service"):
            c1, c2 = st.columns(2)
            with c1:
                nome = st.text_input("Nome completo *", placeholder="Digite o nome do cliente")
                email = st.text_input("E-mail", placeholder="email@exemplo.com")
                cpf = st.text_input("CPF", placeholder="000.000.000-00")
                data_compra = st.date_input("Data da compra", value=date.today(), format="DD/MM/YYYY")
            with c2:
                telefone = st.text_input("Telefone *", placeholder="(19) 99999-9999")
                conheceu = st.selectbox("Como conheceu a SkoobPet?", ["Selecione", "Instagram", "Google", "Indicação", "WhatsApp", "Passando na loja", "Outro"])
                raca = st.text_input("Raça", placeholder="Ex: Shih Tzu")
                sexo = st.selectbox("Sexo", ["", "Macho", "Fêmea"])
            observacoes = st.text_area("Observações", placeholder="Digite observações adicionais...", height=100)
            st.divider()
            c3, c4, c5 = st.columns(3)
            with c3:
                produto = st.selectbox("Produto/Serviço", SERVICE_OPTIONS)
            with c4:
                valor = st.number_input("Valor", min_value=0.0, step=10.0, format="%.2f")
            with c5:
                pagamento = st.selectbox("Forma de pagamento", PAYMENT_OPTIONS)
            c6, c7 = st.columns(2)
            with c6:
                vendedora = st.text_input("Vendedora", placeholder="Nome da vendedora")
            with c7:
                status = st.selectbox("Status", STATUS_OPTIONS, index=0)
            b1, b2 = st.columns([1, 1])
            with b1:
                cancel = st.form_submit_button("Cancelar", use_container_width=True)
            with b2:
                submitted = st.form_submit_button("Próximo  →", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if submitted:
            if not nome or not telefone:
                st.warning("Preencha Nome completo e Telefone.")
            else:
                row = {
                    "Nome": nome,
                    "Telefone": phone_clean(telefone),
                    "CPF": cpf,
                    "E-mail": email,
                    "Data Compra": data_compra.strftime("%d/%m/%Y"),
                    "Mês": data_compra.strftime("%m/%Y"),
                    "Raça": raca,
                    "Sexo": sexo.upper() if sexo else "",
                    "Unidade": UNIDADE_DASHBOARD,
                    "Produto/Serviço": produto,
                    "Valor": money_br(valor),
                    "Forma de Pagamento": pagamento,
                    "Vendedora": vendedora,
                    "Status": status,
                    "Como Conheceu": conheceu,
                    "Observações": observacoes,
                }
                if append_to_sheet(row):
                    st.success("Atendimento salvo com sucesso na planilha!")
                    st.rerun()
    with right:
        st.markdown("<div class='form-card'><div class='chart-title'>Resumo do atendimento</div>", unsafe_allow_html=True)
        st.markdown("<div class='small-muted'>Cliente</div><b>-</b><br><br>", unsafe_allow_html=True)
        st.markdown("<div class='small-muted'>Produtos/Serviços</div><b>0 itens</b><hr>", unsafe_allow_html=True)
        st.markdown(f"<div class='small-muted'>Total</div><div class='kpi-value'>{money_br(0)}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.markdown("<div class='table-card'><div class='chart-title'>Histórico de atendimentos</div>", unsafe_allow_html=True)
    if df.empty:
        st.info("Nenhum dado carregado ainda.")
    else:
        search = st.text_input("Buscar cliente", placeholder="Digite o nome do cliente")
        hist = df.copy()
        if search:
            hist = hist[hist["__nome"].str.contains(search, case=False, na=False) | hist["__telefone"].str.contains(search, case=False, na=False)]
        display_cols = []
        for label in ["Data Compra", "Data da Compra", "Data", "Nome", "Cliente", "Telefone", "Produto/Serviço", "Produto", "Vendedora", "Status", "Valor"]:
            col = find_col(hist, [label])
            if col and col not in display_cols:
                display_cols.append(col)
        st.dataframe(hist[display_cols].tail(50) if display_cols else hist.tail(50), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- FINANCEIRO ----------------
def render_finance(df):
    top1, top2 = st.columns([6, 2])
    with top1:
        page_header("Financeiro")
    with top2:
        if st.button("⬇ Exportar", use_container_width=True):
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("Baixar CSV", csv, "skoobpet_campinas.csv", "text/csv", use_container_width=True)

    faturamento = df["__valor"].sum() if not df.empty else 0
    recebido = df[df["__status"].astype(str).str.contains("pago|fechado|concluído|concluido", case=False, na=False)]["__valor"].sum() if not df.empty else 0
    pendente = max(faturamento - recebido, 0)
    vendas = len(df) if not df.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi_card("Faturamento bruto", money_br(faturamento), "↑ somente Campinas", "💰")
    with c2: kpi_card("Recebido", money_br(recebido), "↑ status pago/fechado", "✅")
    with c3: kpi_card("Pendente", money_br(pendente), "↓ acompanhar recebimentos", "⏳", negative=True)
    with c4: kpi_card("Nº de vendas", vendas, "↑ registros encontrados", "🛒")

    st.write("")
    l, r = st.columns([1.8, .9])
    with l:
        st.markdown("<div class='chart-card'><div class='chart-title'>Faturamento ao longo do tempo</div>", unsafe_allow_html=True)
        if df.empty or pd.isna(df["__data"]).all():
            st.plotly_chart(empty_fig(), use_container_width=True)
        else:
            daily = df.groupby(df["__data"].dt.date)["__valor"].sum().reset_index()
            daily.columns = ["Data", "Faturamento"]
            fig = px.area(daily, x="Data", y="Faturamento")
            fig.update_traces(line=dict(color=SKOOB_PINK, width=3), fillcolor="rgba(212,0,106,.18)")
            st.plotly_chart(style_fig(fig, 315), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with r:
        st.markdown("<div class='chart-card'><div class='chart-title'>Forma de pagamento</div>", unsafe_allow_html=True)
        if df.empty:
            st.plotly_chart(empty_fig(), use_container_width=True)
        else:
            pag = df.groupby("__pagamento")["__valor"].sum().reset_index()
            pag.columns = ["Pagamento", "Valor"]
            fig = px.pie(pag, names="Pagamento", values="Valor", hole=.55, color_discrete_sequence=[SKOOB_NAVY, SKOOB_PINK, "#7c2dbf", "#ff9bd2"])
            st.plotly_chart(style_fig(fig, 315), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    st.markdown("<div class='table-card'><div class='chart-title'>Últimas vendas</div>", unsafe_allow_html=True)
    if df.empty:
        st.info("Nenhuma venda carregada ainda.")
    else:
        display_cols = []
        for label in ["Data Compra", "Data da Compra", "Data", "Nome", "Cliente", "Produto/Serviço", "Produto", "Vendedora", "Forma de Pagamento", "Valor", "Status"]:
            col = find_col(df, [label])
            if col and col not in display_cols:
                display_cols.append(col)
        temp = df.sort_values("__data", ascending=False, na_position="last")
        st.dataframe(temp[display_cols].head(100) if display_cols else temp.head(100), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- MAIN ----------------
def main():
    inject_css()
    if "logged" not in st.session_state:
        st.session_state["logged"] = False

    if not st.session_state["logged"]:
        render_login()
        return

    page = render_sidebar()
    with st.spinner("Carregando dados da planilha..."):
        df = load_data_cached()

    if page.startswith("📊"):
        render_overview(df)
    elif page.startswith("📝"):
        render_form(df)
    else:
        render_finance(df)

if __name__ == "__main__":
    main()
