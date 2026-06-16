import streamlit as st

st.set_page_config(
    page_title="SkoobPet Dashboard",
    page_icon="🐾",
    layout="wide"
)

USUARIOS = {
    "loja1": {"senha": "123456", "nome": "Loja 1", "tipo": "loja"},
    "loja2": {"senha": "123456", "nome": "Loja 2", "tipo": "loja"},
    "loja3": {"senha": "123456", "nome": "Loja 3", "tipo": "loja"},
    "diretoria": {"senha": "123456", "nome": "Diretoria", "tipo": "diretoria"}
}


def aplicar_css():
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(135deg, #1d1564 0%, #120d3f 50%, #9d0139 100%);
            color: #FFFFFF;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stSidebar"] {
            background: #120d3f;
            border-right: 1px solid rgba(255,255,255,0.12);
        }

        label, .stTextInput label {
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }

        .login-container {
            max-width: 430px;
            margin: 70px auto 0 auto;
            padding: 35px;
            border-radius: 24px;
            background: rgba(255, 255, 255, 0.96);
            box-shadow: 0 20px 60px rgba(157, 1, 57, 0.35);
            border: 1px solid rgba(255, 255, 255, 0.22);
            text-align: center;
        }

        .login-title {
            font-size: 38px;
            font-weight: 800;
            color: #1d1564;
            margin-bottom: 5px;
        }

        .login-subtitle {
            color: #4B5563;
            font-size: 15px;
            margin-bottom: 25px;
        }

        .badge {
            display: inline-block;
            padding: 8px 14px;
            border-radius: 999px;
            background: #FCE7F0;
            color: #9d0139;
            font-weight: 700;
            font-size: 13px;
            margin-bottom: 15px;
        }

        div.stButton > button {
            width: 100%;
            height: 46px;
            border-radius: 12px;
            border: none;
            background: #9d0139;
            color: white;
            font-weight: 700;
            font-size: 16px;
        }

        div.stButton > button:hover {
            background: #7c012d;
            color: white;
            border: none;
        }

        .main-card {
            padding: 28px;
            border-radius: 22px;
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid rgba(255,255,255,0.25);
            box-shadow: 0 12px 35px rgba(0, 0, 0, 0.18);
        }

        .main-title {
            font-size: 34px;
            font-weight: 800;
            color: #1d1564;
            margin-bottom: 4px;
        }

        .main-subtitle {
            color: #4B5563;
            font-size: 16px;
        }

        .store-pill {
            display: inline-block;
            padding: 10px 16px;
            border-radius: 999px;
            background: #FCE7F0;
            color: #9d0139;
            font-weight: 800;
            border: 1px solid #9d0139;
        }

        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.96);
            padding: 18px;
            border-radius: 18px;
            border: 1px solid rgba(255,255,255,0.18);
        }

        [data-testid="stMetric"] label,
        [data-testid="stMetric"] div {
            color: #1d1564 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def iniciar_sessao():
    if "logado" not in st.session_state:
        st.session_state.logado = False
    if "usuario" not in st.session_state:
        st.session_state.usuario = None
    if "nome_loja" not in st.session_state:
        st.session_state.nome_loja = None
    if "tipo_usuario" not in st.session_state:
        st.session_state.tipo_usuario = None


def fazer_login(usuario, senha):
    usuario = usuario.strip().lower()

    if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
        st.session_state.logado = True
        st.session_state.usuario = usuario
        st.session_state.nome_loja = USUARIOS[usuario]["nome"]
        st.session_state.tipo_usuario = USUARIOS[usuario]["tipo"]
        st.rerun()
    else:
        st.error("Usuário ou senha incorretos.")


def fazer_logout():
    st.session_state.logado = False
    st.session_state.usuario = None
    st.session_state.nome_loja = None
    st.session_state.tipo_usuario = None
    st.rerun()


def tela_login():
    st.markdown(
        """
        <div class="login-container">
            <div class="badge">Dashboard Comercial</div>
            <div class="login-title">🐾 SkoobPet</div>
            <div class="login-subtitle">Acesse o painel da sua loja</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1, 1.15, 1])

    with col2:
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")

        if st.button("Entrar"):
            fazer_login(usuario, senha)


def tela_dashboard():
    with st.sidebar:
        st.markdown("## 🐾 SkoobPet")
        st.markdown(f"**Acesso:** {st.session_state.nome_loja}")
        st.markdown("---")

        pagina = st.radio(
            "Menu",
            ["Visão Geral", "Comercial", "Vendas", "Financeiro"]
        )

        st.markdown("---")

        if st.button("Sair"):
            fazer_logout()

    st.markdown(
        f"""
        <div class="main-card">
            <div class="main-title">SkoobPet Dashboard</div>
            <div class="main-subtitle">
                Bem-vindo ao painel da <span class="store-pill">{st.session_state.nome_loja}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.write("")

    if pagina == "Visão Geral":
        st.subheader("📊 Visão Geral")
        st.info("Aqui vamos colocar os principais indicadores da loja.")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Leads", "0")
        col2.metric("Vendas", "0")
        col3.metric("Faturamento", "R$ 0,00")
        col4.metric("Clientes em atendimento", "0")

    elif pagina == "Comercial":
        st.subheader("💬 Comercial")
        st.info("Aqui vamos acompanhar os clientes em atendimento.")

    elif pagina == "Vendas":
        st.subheader("🐶 Vendas")
        st.info("Aqui vamos acompanhar as vendas de pets/produtos.")

    elif pagina == "Financeiro":
        st.subheader("💰 Financeiro")
        st.info("Aqui vamos acompanhar valores, faturamento e pagamentos.")


def main():
    aplicar_css()
    iniciar_sessao()

    if st.session_state.logado:
        tela_dashboard()
    else:
        tela_login()


if __name__ == "__main__":
    main()
