import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# =========================
# CONFIGURAÇÃO
# =========================

st.set_page_config(
    page_title="SkoobPet Dashboard",
    page_icon="🐾",
    layout="wide"
)

SPREADSHEET_ID = "1Q0mLvOBxEGCojUITBLxCXRTpXVMAHE3ngvGsa2Cgf9Q"
SHEET_NAME = "Clear"

LOGIN_USER = "admin"
LOGIN_PASS = "skoobpet2026"

# =========================
# CORES SKOOBPET
# =========================

NAVY = "#05045C"
BLUE = "#11147A"
PINK = "#D6006F"
PINK_2 = "#FF0A83"
LIGHT_BG = "#FFF7FC"
CARD = "#FFFFFF"
TEXT = "#05045C"
MUTED = "#6B6B8D"
GREEN = "#00A86B"
RED = "#E53935"

# =========================
# CSS
# =========================

st.markdown(f"""
<style>
.stApp {{
    background: linear-gradient(135deg, #fff7fc 0%, #f8f1ff 45%, #fff 100%);
}}

[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {NAVY} 0%, #09085f 60%, #030239 100%);
}}

[data-testid="stSidebar"] * {{
    color: white !important;
}}

.block-container {{
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}}

h1, h2, h3 {{
    color: {TEXT};
    font-weight: 800;
}}

.card {{
    background: {CARD};
    border-radius: 18px;
    padding: 22px;
    box-shadow: 0 8px 25px rgba(5,4,92,0.08);
    border: 1px solid rgba(214,0,111,0.08);
}}

.metric-card {{
    background: white;
    border-radius: 18px;
    padding: 20px;
    box-shadow: 0 8px 25px rgba(5,4,92,0.08);
    border: 1px solid rgba(214,0,111,0.10);
    min-height: 125px;
}}

.metric-title {{
    color: {MUTED};
    font-size: 14px;
    font-weight: 700;
}}

.metric-value {{
    color: {TEXT};
    font-size: 30px;
    font-weight: 900;
    margin-top: 8px;
}}

.metric-sub {{
    color: {GREEN};
    font-size: 13px;
    margin-top: 8px;
}}

.stButton > button {{
    background: linear-gradient(90deg, {BLUE}, {PINK});
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.7rem 1.5rem;
    font-weight: 700;
}}

.stButton > button:hover {{
    opacity: 0.92;
    color: white;
}}

input, textarea, select {{
    border-radius: 12px !important;
}}

div[data-testid="stMetric"] {{
    background: white;
    padding: 18px;
    border-radius: 18px;
    box-shadow: 0 8px 25px rgba(5,4,92,0.08);
}}

.logo-title {{
    font-size: 28px;
    font-weight: 900;
    color: white;
    text-align: center;
    margin-bottom: 30px;
}}

.small-muted {{
    color: {MUTED};
    font-size: 13px;
}}

.table-card {{
    background: white;
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 8px 25px rgba(5,4,92,0.08);
}}
</style>
""", unsafe_allow_html=True)

# =========================
# GOOGLE SHEETS
# =========================

@st.cache_resource
def get_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
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


# =========================
# LOGIN
# =========================

def login_page():
    col1, col2 = st.columns([1.2, 1])

    with col1:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="text-align:center;">
            <div style="font-size:64px;">🐶🐱</div>
            <h1 style="color:{NAVY}; margin-bottom:0;">SkoobPet</h1>
            <h3 style="color:{PINK};">Bem-vindo(a) de volta!</h3>
            <p style="color:{MUTED}; font-size:16px;">
                Faça login para acessar o painel da unidade Campinas.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)

        st.subheader("Acessar conta")
        user = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")

        if st.button("Entrar", use_container_width=True):
            if user == LOGIN_USER and password == LOGIN_PASS:
                st.session_state["logged"] = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos.")

        st.markdown("</div>", unsafe_allow_html=True)


# =========================
# SIDEBAR
# =========================

def sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="logo-title">
            🐶🐱<br>SkoobPet
        </div>
        """, unsafe_allow_html=True)

        page = st.radio(
            "Menu",
            ["Visão geral", "Formulário", "Financeiro"],
            label_visibility="collapsed"
        )

        st.markdown("<br><br><br>", unsafe_allow_html=True)

        if st.button("Sair"):
            st.session_state["logged"] = False
            st.rerun()

    return page


# =========================
# COMPONENTES
# =========================

def metric_card(title, value, sub="+ 0% vs período anterior"):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def money(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


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
        max_value=max_date
    )

    if isinstance(period, tuple) and len(period) == 2:
        start, end = period
        df = df[
            (df["Data Compra"].dt.date >= start) &
            (df["Data Compra"].dt.date <= end)
        ]

    return df


# =========================
# VISÃO GERAL
# =========================

def page_overview(df):
    st.title("Visão geral")
    st.markdown("📍 Campinas")

    df = filter_period(df)

    total_contatos = len(df)
    total_vendas = len(df)
    faturamento = df["Valor"].sum() if "Valor" in df.columns else 0
    ticket = faturamento / total_vendas if total_vendas else 0

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card("Contatos no mês", total_contatos, "↑ Campinas")
    with c2:
        metric_card("Vendas no mês", total_vendas, "↑ Unidade Campinas")
    with c3:
        metric_card("Ticket médio", money(ticket), "↑ Média do período")
    with c4:
        metric_card("Faturamento no mês", money(faturamento), "↑ Total vendido")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1.2, 1.2, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Contatos por dia")

        if "Data Compra" in df.columns and not df.empty:
            chart = df.groupby(df["Data Compra"].dt.date).size().reset_index(name="Contatos")
            fig = px.line(chart, x="Data Compra", y="Contatos", markers=True)
            fig.update_traces(line_color=PINK)
            fig.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10))
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
            fig.update_traces(line_color=BLUE)
            fig.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados para exibir.")

        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Vendas por unidade")

        fig = go.Figure(data=[go.Pie(
            labels=["Campinas"],
            values=[100],
            hole=.55,
            marker=dict(colors=[PINK])
        )])

        fig.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    col4, col5, col6 = st.columns([1.2, 1.2, 1])

    with col4:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Raças mais vendidas")

        if "Raça" in df.columns and not df.empty:
            chart = df["Raça"].value_counts().head(8).reset_index()
            chart.columns = ["Raça", "Quantidade"]
            fig = px.bar(chart, x="Quantidade", y="Raça", orientation="h")
            fig.update_traces(marker_color=PINK)
            fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Coluna Raça não encontrada.")

        st.markdown("</div>", unsafe_allow_html=True)

    with col5:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Vendas por vendedora")

        seller_col = None
        for c in ["Vendedora", "Vendedor", "Responsável", "Responsavel"]:
            if c in df.columns:
                seller_col = c
                break

        if seller_col and not df.empty:
            chart = df[seller_col].value_counts().head(8).reset_index()
            chart.columns = ["Vendedora", "Quantidade"]
            fig = px.bar(chart, x="Vendedora", y="Quantidade")
            fig.update_traces(marker_color=PINK)
            fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Coluna de vendedora não encontrada.")

        st.markdown("</div>", unsafe_allow_html=True)

    with col6:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Resumo por status")

        status_col = None
        for c in ["Status", "Status Venda Pedigree", "Status Venda"]:
            if c in df.columns:
                status_col = c
                break

        if status_col and not df.empty:
            status = df[status_col].value_counts().reset_index()
            status.columns = ["Status", "Quantidade"]
            st.dataframe(status, use_container_width=True, hide_index=True)
        else:
            st.info("Sem coluna de status.")

        st.markdown("</div>", unsafe_allow_html=True)


# =========================
# FORMULÁRIO
# =========================

def page_form(df):
    st.title("Formulário")
    st.markdown("📍 Campinas")

    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.subheader("Dados do cliente")

    c1, c2 = st.columns(2)

    with c1:
        nome = st.text_input("Nome completo")
        cpf = st.text_input("CPF")
        telefone = st.text_input("Telefone")
        email = st.text_input("E-mail")

    with c2:
        data_compra = st.date_input("Data da compra", value=datetime.today())
        raca = st.text_input("Raça")
        sexo = st.selectbox("Sexo", ["", "MACHO", "FÊMEA"])
        cor = st.text_input("Cor")

    st.subheader("Dados da venda")

    c3, c4, c5 = st.columns(3)

    with c3:
        valor = st.number_input("Valor", min_value=0.0, step=10.0)
    with c4:
        vendedora = st.text_input("Vendedora")
    with c5:
        status = st.selectbox(
            "Status",
            ["Novo Lead", "Conversando", "Sem interesse", "Aguardando", "Fechado", "Pago", "Pendente"]
        )

    observacoes = st.text_area("Observações")

    if st.button("Salvar atendimento", use_container_width=True):
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
            observacoes
        ]

        append_row(new_row)
        st.success("Atendimento salvo com sucesso!")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="table-card">', unsafe_allow_html=True)
    st.subheader("Histórico de atendimentos")

    if not df.empty:
        st.dataframe(df.tail(20), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum atendimento encontrado.")

    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# FINANCEIRO
# =========================

def page_financial(df):
    st.title("Financeiro")
    st.markdown("📍 Campinas")

    df = filter_period(df)

    faturamento = df["Valor"].sum() if "Valor" in df.columns else 0
    recebido = faturamento
    pendente = 0
    vendas = len(df)

    status_col = None
    for c in ["Status", "Status Venda Pedigree", "Status Venda"]:
        if c in df.columns:
            status_col = c
            break

    if status_col:
        pendente_df = df[df[status_col].str.upper().str.contains("PENDENTE|AGUARDANDO", na=False)]
        pendente = pendente_df["Valor"].sum()
        recebido = faturamento - pendente

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card("Faturamento bruto", money(faturamento), "↑ Período selecionado")
    with c2:
        metric_card("Recebido", money(recebido), "↑ Valores pagos")
    with c3:
        metric_card("Pendente", money(pendente), "↓ A receber")
    with c4:
        metric_card("Nº de vendas", vendas, "↑ Total de registros")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.6, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Faturamento ao longo do tempo")

        if "Data Compra" in df.columns and not df.empty:
            chart = df.groupby(df["Data Compra"].dt.date)["Valor"].sum().reset_index()
            fig = px.area(chart, x="Data Compra", y="Valor")
            fig.update_traces(line_color=PINK, fillcolor="rgba(214,0,111,0.18)")
            fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados para exibir.")

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Forma de pagamento")

        pay_col = None
        for c in ["Forma de Pagamento", "Pagamento", "Forma Pagamento"]:
            if c in df.columns:
                pay_col = c
                break

        if pay_col and not df.empty:
            chart = df[pay_col].value_counts().reset_index()
            chart.columns = ["Forma", "Quantidade"]
            fig = px.pie(chart, names="Forma", values="Quantidade", hole=.55)
            fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=10))
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


# =========================
# MAIN
# =========================

def main():
    if "logged" not in st.session_state:
        st.session_state["logged"] = False

    if not st.session_state["logged"]:
        login_page()
        return

    page = sidebar()

    try:
        df = load_data()
    except Exception as e:
        st.error("Erro ao carregar a planilha. Verifique o secrets.toml e o compartilhamento da planilha com o e-mail da conta de serviço.")
        st.exception(e)
        return

    if page == "Visão geral":
        page_overview(df)

    elif page == "Formulário":
        page_form(df)

    elif page == "Financeiro":
        page_financial(df)


if __name__ == "__main__":
    main()
