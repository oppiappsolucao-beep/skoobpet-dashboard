
import base64
import json
import re
from datetime import date, datetime

import gspread
import pandas as pd
import plotly.express as px
import streamlit as st
from google.oauth2.service_account import Credentials


# =========================
# CONFIGURAÇÕES PRINCIPAIS
# =========================
APP_TITLE = "Dashboard SkoobPet Campinas"
SHEET_ID = "1Q0mLvOBxEGCojUITBLxCXRtpXVMAHE3ngvGsa2Cgf9Q"
WORKSHEET_NAME = "Clear"
UNIDADE_PADRAO = "CAMPINAS"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]

LOGO_PATH = "assets/skoobpet.png"


# =========================
# CORES SKOOBPET
# =========================
NAVY = "#21156E"
BLUE = "#2B2B87"
WINE = "#B00046"
PINK = "#D40062"
BG = "#F4F1F8"
CARD = "#FFFFFF"
TEXT = "#17142E"
MUTED = "#667085"


# =========================
# CONFIG STREAMLIT
# =========================
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🐶",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================
# CSS
# =========================
def inject_css():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

        * {{
            font-family: 'Inter', sans-serif;
        }}

        .stApp {{
            background: linear-gradient(135deg, #ffffff 0%, {BG} 45%, #f8eaf1 100%);
            color: {TEXT};
        }}

        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #ffffff 0%, #f6f3fb 55%, #fff0f6 100%);
            border-right: 1px solid rgba(33, 21, 110, 0.12);
        }}

        section[data-testid="stSidebar"] .stMarkdown,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] span {{
            color: {TEXT} !important;
        }}

        h1, h2, h3 {{
            color: {TEXT};
            font-weight: 800;
        }}

        .main-title {{
            font-size: 42px;
            line-height: 1.05;
            font-weight: 900;
            margin-bottom: 4px;
            color: {NAVY};
        }}

        .main-subtitle {{
            color: {MUTED};
            font-size: 15px;
            margin-bottom: 22px;
        }}

        .brand-card {{
            background: linear-gradient(135deg, {NAVY} 0%, {BLUE} 58%, {WINE} 100%);
            border-radius: 28px;
            padding: 22px;
            color: white;
            box-shadow: 0 18px 45px rgba(33, 21, 110, 0.18);
            margin-bottom: 20px;
        }}

        .brand-card h2 {{
            color: white;
            margin: 10px 0 0 0;
            font-size: 24px;
        }}

        .brand-card p {{
            color: rgba(255,255,255,0.86);
            margin: 6px 0 0 0;
            font-size: 13px;
        }}

        .kpi-card {{
            background: {CARD};
            padding: 22px;
            border-radius: 24px;
            border: 1px solid rgba(33, 21, 110, 0.10);
            box-shadow: 0 12px 30px rgba(33, 21, 110, 0.08);
            min-height: 138px;
        }}

        .kpi-icon {{
            width: 42px;
            height: 42px;
            border-radius: 15px;
            background: linear-gradient(135deg, {WINE}, {PINK});
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            margin-bottom: 12px;
        }}

        .kpi-label {{
            color: {MUTED};
            font-size: 13px;
            font-weight: 700;
            margin-bottom: 4px;
        }}

        .kpi-value {{
            color: {NAVY};
            font-size: 30px;
            font-weight: 900;
            line-height: 1;
        }}

        .kpi-help {{
            color: {WINE};
            font-size: 12px;
            font-weight: 700;
            margin-top: 8px;
        }}

        .chart-box {{
            background: {CARD};
            border-radius: 24px;
            padding: 18px 18px 8px 18px;
            border: 1px solid rgba(33, 21, 110, 0.10);
            box-shadow: 0 12px 30px rgba(33, 21, 110, 0.08);
            margin-bottom: 20px;
        }}

        .chart-title {{
            font-size: 19px;
            font-weight: 900;
            color: {NAVY};
            margin: 0;
        }}

        .chart-subtitle {{
            color: {MUTED};
            font-size: 13px;
            margin: 3px 0 12px 0;
        }}

        div.stButton > button,
        div.stDownloadButton > button {{
            border-radius: 16px;
            border: none;
            background: linear-gradient(135deg, {WINE}, {PINK});
            color: white;
            font-weight: 800;
            padding: 0.7rem 1rem;
            box-shadow: 0 10px 22px rgba(176, 0, 70, 0.18);
        }}

        div.stButton > button:hover,
        div.stDownloadButton > button:hover {{
            filter: brightness(1.05);
            color: white;
        }}

        .dataframe {{
            border-radius: 18px !important;
            overflow: hidden;
        }}

        [data-testid="stMetricValue"] {{
            color: {NAVY};
        }}

        .small-note {{
            font-size: 12px;
            color: {MUTED};
        }}

        .sidebar-logo {{
            display: flex;
            justify-content: center;
            margin-bottom: 12px;
        }}

        .status-pill {{
            padding: 7px 10px;
            border-radius: 999px;
            background: #fff0f6;
            border: 1px solid rgba(176,0,70,0.12);
            font-weight: 800;
            color: {WINE};
            display: inline-block;
            margin-bottom: 8px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================
# FUNÇÕES AUXILIARES
# =========================
def normalize_col(col):
    col = str(col).strip()
    col = re.sub(r"\s+", " ", col)
    return col


def find_col(df, candidates):
    normalized = {normalize_col(c).lower(): c for c in df.columns}
    for cand in candidates:
        key = normalize_col(cand).lower()
        if key in normalized:
            return normalized[key]
    return None


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


def month_label(dt):
    if pd.isna(dt):
        return ""
    return f"{dt.month:02d}/{dt.year}"


def safe_upper(value):
    if pd.isna(value):
        return ""
    return str(value).strip().upper()


def fig_layout(fig):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=TEXT, family="Inter"),
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
    )
    fig.update_xaxes(gridcolor="rgba(33, 21, 110, 0.08)")
    fig.update_yaxes(gridcolor="rgba(33, 21, 110, 0.08)")
    return fig


def chart_header(title, subtitle):
    st.markdown(
        f"""
        <div>
            <p class="chart-title">{title}</p>
            <p class="chart-subtitle">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi(icon, label, value, help_text="Base atual"):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-icon">{icon}</div>
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-help">{help_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def image_to_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return ""


@st.cache_resource(ttl=3600)
def get_client():
    if "gcp_service_account" not in st.secrets:
        st.error("Configure o segredo gcp_service_account no Streamlit.")
        st.stop()

    info = dict(st.secrets["gcp_service_account"])

    if "private_key" in info:
        info["private_key"] = info["private_key"].replace("\\n", "\n")

    credentials = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(credentials)


@st.cache_data(ttl=60, show_spinner=False)
def load_data():
    client = get_client()
    sh = client.open_by_key(SHEET_ID)
    ws = sh.worksheet(WORKSHEET_NAME)
    rows = ws.get_all_records()
    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df.columns = [normalize_col(c) for c in df.columns]

    col_data = find_col(df, ["Data Compra", "Data da Compra", "Data da venda", "Data Venda"])
    col_mes = find_col(df, ["Mês", "Mes", "Mês da Compra", "Mês da Compra do Cliente"])
    col_unidade = find_col(df, ["Unidade", "Loja"])
    col_valor = find_col(df, ["Valor", "Valor Venda", "Valor da Venda", "Total"])
    col_status = find_col(df, ["Status", "Status Venda Pedigree", "Status Comercial"])
    col_nome = find_col(df, ["Nome", "Cliente", "Nome completo"])
    col_tel = find_col(df, ["Telefone", "Celular", "WhatsApp"])
    col_raca = find_col(df, ["Raça", "Raca"])
    col_sexo = find_col(df, ["Sexo"])
    col_cor = find_col(df, ["Cor"])
    col_vendedora = find_col(df, ["Vendedora", "Vendedor", "Consultora"])
    col_contato = find_col(df, ["Contato", "Tipo contato", "Etapa contato", "1º contato", "Primeiro contato"])

    df["_data_compra"] = pd.to_datetime(df[col_data], dayfirst=True, errors="coerce") if col_data else pd.NaT

    if col_mes:
        df["_mes"] = df[col_mes].astype(str).str.strip()
    else:
        df["_mes"] = df["_data_compra"].apply(month_label)

    if col_unidade:
        df["_unidade"] = df[col_unidade].apply(safe_upper)
    else:
        df["_unidade"] = ""

    df["_valor"] = df[col_valor].apply(parse_money) if col_valor else 0.0
    df["_status"] = df[col_status].astype(str).str.strip() if col_status else "Sem status"
    df["_nome"] = df[col_nome].astype(str).str.strip() if col_nome else ""
    df["_telefone"] = df[col_tel].apply(clean_phone) if col_tel else ""
    df["_raca"] = df[col_raca].astype(str).str.strip().str.upper() if col_raca else "Não informado"
    df["_sexo"] = df[col_sexo].astype(str).str.strip().str.upper() if col_sexo else "Não informado"
    df["_cor"] = df[col_cor].astype(str).str.strip().str.upper() if col_cor else "Não informado"
    df["_vendedora"] = df[col_vendedora].astype(str).str.strip() if col_vendedora else "Sem vendedora"
    df["_contato"] = df[col_contato].astype(str).str.strip() if col_contato else ""

    # Filtra SOMENTE Campinas
    if col_unidade:
        df = df[df["_unidade"].str.contains("CAMPINAS", na=False)].copy()

    return df


def get_month_options(df):
    meses = sorted([m for m in df["_mes"].dropna().astype(str).unique() if m and m.lower() != "nan"])
    return ["Todos"] + meses


def filter_data(df, mes, busca):
    filtered = df.copy()

    if mes and mes != "Todos":
        filtered = filtered[filtered["_mes"].astype(str) == mes]

    if busca:
        b = busca.strip().lower()
        mask = (
            filtered["_nome"].astype(str).str.lower().str.contains(b, na=False)
            | filtered["_telefone"].astype(str).str.lower().str.contains(b, na=False)
            | filtered.astype(str).apply(lambda row: row.str.lower().str.contains(b, na=False).any(), axis=1)
        )
        filtered = filtered[mask]

    return filtered


def sidebar():
    logo_b64 = image_to_base64(LOGO_PATH)

    with st.sidebar:
        if logo_b64:
            st.markdown(
                f"""
                <div class="sidebar-logo">
                    <img src="data:image/png;base64,{logo_b64}" style="width: 165px; border-radius: 18px;">
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown(
            f"""
            <div class="brand-card">
                <div style="font-size: 34px;">🐾</div>
                <h2>SkoobPet</h2>
                <p>Dashboard exclusivo da unidade Campinas</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        page = st.radio(
            "Menu",
            ["Visão geral", "Formulário", "Financeiro"],
            label_visibility="collapsed",
        )

        st.divider()
        st.markdown(
            """
            <div class="small-note">
            Dados conectados direto da planilha Google Sheets.<br>
            Filtro fixo: <b>Campinas</b>.
            </div>
            """,
            unsafe_allow_html=True,
        )

    return page


# =========================
# PÁGINA VISÃO GERAL
# =========================
def page_overview(df):
    st.markdown('<div class="main-title">Visão Geral</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="main-subtitle">Acompanhe os contatos, vendas e desempenho da unidade Campinas em tempo real.</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1, 0.7])
    with col1:
        mes = st.selectbox("Filtrar por mês", get_month_options(df), index=0)
    with col2:
        busca = st.text_input("Buscar por nome, telefone ou qualquer informação", placeholder="Digite para pesquisar...")
    with col3:
        st.write("")
        st.write("")
        if st.button("🔄 Atualizar dados", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    filtered = filter_data(df, mes, busca)

    hoje = pd.Timestamp(date.today())
    chamados_hoje = int((filtered["_data_compra"].dt.date == hoje.date()).sum()) if "_data_compra" in filtered else 0
    inicio_semana = hoje - pd.Timedelta(days=hoje.weekday())
    chamados_semana = int((filtered["_data_compra"] >= inicio_semana).sum()) if "_data_compra" in filtered else 0
    chamados_mes = len(filtered)
    total_vendas = filtered["_valor"].sum()
    ticket = total_vendas / len(filtered) if len(filtered) else 0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi("☎️", "Chamados hoje", chamados_hoje)
    with k2:
        kpi("📅", "Chamados na semana", chamados_semana)
    with k3:
        kpi("📊", "Chamados no período", chamados_mes)
    with k4:
        kpi("💰", "Faturamento filtrado", f"R$ {total_vendas:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

    st.write("")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        chart_header("☎️ Contatos por mês", "Distribuição mensal dos contatos da unidade Campinas")
        if filtered.empty:
            st.info("Sem dados para exibir.")
        else:
            tmp = filtered.groupby("_mes", dropna=False).size().reset_index(name="Quantidade")
            fig = px.bar(tmp, x="_mes", y="Quantidade", text="Quantidade", color_discrete_sequence=[NAVY, WINE])
            fig.update_traces(textposition="outside")
            fig = fig_layout(fig)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        chart_header("🏢 Vendas por unidade", "Este dashboard mostra somente Campinas")
        tmp = pd.DataFrame({"Unidade": ["CAMPINAS"], "Quantidade": [len(filtered)]})
        fig = px.bar(tmp, x="Unidade", y="Quantidade", text="Quantidade", color_discrete_sequence=[NAVY])
        fig.update_traces(textposition="outside")
        fig = fig_layout(fig)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        chart_header("🐶 Raças mais vendidas", "Top 10 raças no período filtrado")
        if filtered.empty:
            st.info("Sem dados para exibir.")
        else:
            tmp = filtered["_raca"].replace("", "Não informado").value_counts().head(10).reset_index()
            tmp.columns = ["Raça", "Quantidade"]
            fig = px.bar(tmp, x="Raça", y="Quantidade", text="Quantidade", color_discrete_sequence=[NAVY, WINE, BLUE])
            fig.update_traces(textposition="outside")
            fig = fig_layout(fig)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c4:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        chart_header("🏆 Vendas por vendedora", "Quantidade de registros por vendedora")
        if filtered.empty:
            st.info("Sem dados para exibir.")
        else:
            tmp = filtered["_vendedora"].replace("", "Sem vendedora").value_counts().head(12).reset_index()
            tmp.columns = ["Vendedora", "Quantidade"]
            fig = px.bar(tmp, x="Vendedora", y="Quantidade", text="Quantidade", color_discrete_sequence=[NAVY, WINE, BLUE])
            fig.update_traces(textposition="outside")
            fig = fig_layout(fig)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    c5, c6 = st.columns(2)
    with c5:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        chart_header("📌 Resumo por status", "Distribuição atual dos leads")
        if filtered.empty:
            st.info("Sem dados para exibir.")
        else:
            tmp = filtered["_status"].replace("", "Sem status").value_counts().reset_index()
            tmp.columns = ["Status", "Quantidade"]
            fig = px.pie(tmp, names="Status", values="Quantidade", hole=0.48, color_discrete_sequence=[NAVY, WINE, BLUE, PINK])
            fig = fig_layout(fig)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c6:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        chart_header("💳 Financeiro por mês", "Soma dos valores no período")
        if filtered.empty:
            st.info("Sem dados para exibir.")
        else:
            tmp = filtered.groupby("_mes", dropna=False)["_valor"].sum().reset_index()
            tmp.columns = ["Mês", "Valor"]
            fig = px.bar(tmp, x="Mês", y="Valor", text="Valor", color_discrete_sequence=[WINE])
            fig.update_traces(texttemplate="R$ %{text:,.2f}", textposition="outside")
            fig = fig_layout(fig)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### 📋 Registros filtrados")
    show_cols = [c for c in ["Nome", "Telefone", "CPF", "E-mail", "Data Compra", "Mês", "Raça", "Sexo", "Cor", "Unidade", "Vendedora", "Valor", "Status"] if c in filtered.columns]
    if show_cols:
        st.dataframe(filtered[show_cols], use_container_width=True, hide_index=True)
    else:
        st.dataframe(filtered.drop(columns=[c for c in filtered.columns if c.startswith("_")], errors="ignore"), use_container_width=True, hide_index=True)


# =========================
# PÁGINA FORMULÁRIO
# =========================
def append_row_to_sheet(row_dict):
    client = get_client()
    sh = client.open_by_key(SHEET_ID)
    ws = sh.worksheet(WORKSHEET_NAME)

    headers = [normalize_col(h) for h in ws.row_values(1)]
    new_row = []

    for h in headers:
        new_row.append(row_dict.get(h, ""))

    ws.append_row(new_row, value_input_option="USER_ENTERED")


def page_form(df):
    st.markdown('<div class="main-title">Formulário</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="main-subtitle">Cadastre novos clientes diretamente na planilha da SkoobPet Campinas.</div>',
        unsafe_allow_html=True,
    )

    with st.form("form_cadastro", clear_on_submit=True):
        st.markdown('<span class="status-pill">Unidade fixa: Campinas</span>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            nome = st.text_input("Nome do cliente")
            telefone = st.text_input("Telefone / WhatsApp")
            cpf = st.text_input("CPF")
            email = st.text_input("E-mail")
            data_compra = st.date_input("Data da compra", value=date.today(), format="DD/MM/YYYY")
        with c2:
            raca = st.text_input("Raça")
            sexo = st.selectbox("Sexo", ["", "FÊMEA", "MACHO"])
            cor = st.text_input("Cor")
            vendedora = st.text_input("Vendedora")
            valor = st.number_input("Valor da venda", min_value=0.0, step=10.0, format="%.2f")

        status = st.selectbox(
            "Status",
            ["Novo Lead", "Conversando", "Sem interesse", "Não responde", "Fechado", "Proposta", "Reunião"],
        )

        submitted = st.form_submit_button("💾 Salvar cadastro")

    if submitted:
        data_str = data_compra.strftime("%d/%m/%Y")
        mes_str = data_compra.strftime("%m/%Y")
        valor_str = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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
            "Unidade": UNIDADE_PADRAO,
            "Vendedora": vendedora,
            "Valor": valor_str,
            "Status": status,
        }

        try:
            append_row_to_sheet(row)
            st.cache_data.clear()
            st.success("Cadastro enviado para a planilha com sucesso!")
        except Exception as e:
            st.error(f"Não foi possível salvar na planilha: {e}")


# =========================
# PÁGINA FINANCEIRO
# =========================
def page_finance(df):
    st.markdown('<div class="main-title">Financeiro</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="main-subtitle">Resumo financeiro da unidade Campinas com base nos valores da planilha.</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1, 1])
    with c1:
        mes = st.selectbox("Filtrar por mês", get_month_options(df), index=0, key="fin_mes")
    with c2:
        busca = st.text_input("Buscar", placeholder="Nome, telefone, vendedora...", key="fin_busca")

    filtered = filter_data(df, mes, busca)

    faturamento = filtered["_valor"].sum()
    qtd = len(filtered)
    ticket = faturamento / qtd if qtd else 0
    vendas_fechadas = int(filtered["_status"].astype(str).str.lower().str.contains("fechado|vend", na=False).sum())

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi("💰", "Faturamento", f"R$ {faturamento:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    with k2:
        kpi("🧾", "Registros", qtd)
    with k3:
        kpi("🎟️", "Ticket médio", f"R$ {ticket:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    with k4:
        kpi("✅", "Fechados", vendas_fechadas)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        chart_header("💳 Faturamento por mês", "Soma dos valores por mês")
        if filtered.empty:
            st.info("Sem dados para exibir.")
        else:
            tmp = filtered.groupby("_mes", dropna=False)["_valor"].sum().reset_index()
            tmp.columns = ["Mês", "Valor"]
            fig = px.line(tmp, x="Mês", y="Valor", markers=True, color_discrete_sequence=[WINE])
            fig = fig_layout(fig)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c4:
        st.markdown('<div class="chart-box">', unsafe_allow_html=True)
        chart_header("🏆 Valor por vendedora", "Ranking financeiro por vendedora")
        if filtered.empty:
            st.info("Sem dados para exibir.")
        else:
            tmp = filtered.groupby("_vendedora", dropna=False)["_valor"].sum().sort_values(ascending=False).head(12).reset_index()
            tmp.columns = ["Vendedora", "Valor"]
            fig = px.bar(tmp, x="Vendedora", y="Valor", text="Valor", color_discrete_sequence=[NAVY, WINE, BLUE])
            fig.update_traces(texttemplate="R$ %{text:,.2f}", textposition="outside")
            fig = fig_layout(fig)
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("### 📋 Lançamentos financeiros")
    show_cols = [c for c in ["Nome", "Telefone", "Data Compra", "Mês", "Unidade", "Vendedora", "Valor", "Status"] if c in filtered.columns]
    if show_cols:
        st.dataframe(filtered[show_cols], use_container_width=True, hide_index=True)
    else:
        st.dataframe(filtered.drop(columns=[c for c in filtered.columns if c.startswith("_")], errors="ignore"), use_container_width=True, hide_index=True)


# =========================
# MAIN
# =========================
def main():
    inject_css()
    page = sidebar()

    with st.spinner("Carregando dados da planilha..."):
        df = load_data()

    if df.empty:
        st.warning("A planilha está vazia ou não foi possível carregar os dados.")
        st.stop()

    if page == "Visão geral":
        page_overview(df)
    elif page == "Formulário":
        page_form(df)
    elif page == "Financeiro":
        page_finance(df)


if __name__ == "__main__":
    main()
