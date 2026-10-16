"""
SGIH - Sistema de Gestão Inteligente de Helpdesk
=================================================
VARIANTE 2: consulta em SEGUNDO PLANO (background thread).
O usuário clica em "Análise de Chamadas", a busca do CDR começa
numa thread separada, e o usuário PODE voltar para "Visão Geral"
ou qualquer outro menu enquanto ela roda.
Um badge na sidebar mostra o progresso em tempo real.
"""
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from modules.visao_geral import renderizar_botao_audio

# ==========================================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================================
st.set_page_config(
    layout="wide",
    page_title="SGIH",
    page_icon="🖥️"
)

# ==========================================================
# CSS
# ==========================================================
st.markdown("""
<style>
section[data-testid="stSidebar"] {
    background-color: #111827;
    border-right: 1px solid #232b3d;
}
.sgih-title {
    color: #ffffff;
    font-size: 16px;
    font-weight: 600;
    margin-bottom: 0px;
}
.sgih-subtitle {
    color: #7d879c;
    font-size: 11px;
    line-height: 1.3;
    margin-bottom: 14px;
}
.badge-job {
    background: #0c2a4a;
    border: 1px solid #1d4ed8;
    border-radius: 8px;
    padding: 8px 10px;
    margin-bottom: 10px;
    color: #85b7eb;
    font-size: 12px;
}
div[data-testid="stSidebar"] button {
    text-align: left;
    background-color: transparent;
    border: none;
    color: #9fb0cc;
}
div[data-testid="stSidebar"] button:hover {
    background-color: #1a2233;
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

# ==========================================================
# ESTADO DA SESSÃO
# ==========================================================
if "menu" not in st.session_state:
    st.session_state.menu = "visao_geral"
if "card" not in st.session_state:
    st.session_state.card = None
if "sidebar_expandida" not in st.session_state:
    st.session_state.sidebar_expandida = True
if "refresh_rate" not in st.session_state:
    st.session_state.refresh_rate = 30
# Dicionário de jobs em segundo plano
if "jobs" not in st.session_state:
    st.session_state.jobs = {}

# ==========================================================
# FUNÇÃO PARA TROCAR DE MENU
# ==========================================================
def ir_para(menu, card=None):
    st.session_state.menu = menu
    st.session_state.card = card
    st.rerun()

# ==========================================================
# AUTOREFRESH
# ==========================================================
algum_job_rodando = any(
    j.get("status") == "running"
    for j in st.session_state.jobs.values()
)
if algum_job_rodando:
    st_autorefresh(
        interval=2000,
        key="autorefresh_jobs"
    )

# ==========================================================
# SIDEBAR
# ==========================================================
with st.sidebar:
    # ------------------------------------------------------
    # CABEÇALHO DA SIDEBAR
    # ------------------------------------------------------
    col_titulo, col_toggle = st.columns([5, 1])
    with col_titulo:
        if st.session_state.sidebar_expandida:
            st.markdown(
                '<p class="sgih-title">⚡SGIH</p>',
                unsafe_allow_html=True
            )
            st.markdown(
                '<p class="sgih-subtitle">'
                'Sistema de Gestão Inteligente de ServiceDesk'
                '</p>',
                unsafe_allow_html=True
            )

    # ------------------------------------------------------
    # BOTÃO PARA EXPANDIR/RECOLHER SIDEBAR
    # ------------------------------------------------------
    with col_toggle:
        if st.button(
            "☰",
            key="btn_toggle_sidebar"
        ):
            st.session_state.sidebar_expandida = (
                not st.session_state.sidebar_expandida
            )
            st.rerun()

    st.divider()

    # ======================================================
    # CONFIGURAÇÕES
    # ======================================================
    if st.session_state.sidebar_expandida:
        with st.expander(
            "⚙️ Configurações",
            expanded=False
        ):
            st.session_state.refresh_rate = st.slider(
                "Atualização (segundos)",
                10,
                300,
                st.session_state.refresh_rate,
                5
            )

            # Botão de som do Kanban (dentro do expansor)
            st.markdown("---")
            renderizar_botao_audio()
    else:
        st.button(
            "⚙️",
            key="btn_config_icon",
            help="Configurações de atualização"
        )

    # ======================================================
    # BADGE DE JOBS
    # ======================================================
    job_analise = st.session_state.jobs.get(
        "analise_chamadas"
    )
    if (
        job_analise
        and job_analise["status"] == "running"
    ):
        pct = int(
            job_analise["progresso"] * 100
        )
        if st.session_state.sidebar_expandida:
            st.markdown(
                f'''
                <div class="badge-job">
                    🔄 Análise de chamadas: {pct}%<br>
                    {job_analise["texto"]}
                </div>
                ''',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'''
                <div class="badge-job">
                    🔄 {pct}%
                </div>
                ''',
                unsafe_allow_html=True
            )
    elif (
        job_analise
        and job_analise["status"] == "done"
    ):
        if st.session_state.sidebar_expandida:
            st.markdown(
                '''
                <div class="badge-job">
                    ✅ Análise de chamadas pronta
                </div>
                ''',
                unsafe_allow_html=True
            )

    # ======================================================
    # MENU LATERAL
    # ======================================================
    st.divider()

    # ------------------------------------------------------
    # NOMES DOS BOTÕES
    # ------------------------------------------------------
    label_visao = (
        "🏠 Visão Geral"
        if st.session_state.sidebar_expandida
        else "🏠"
    )
    label_chamadas = (
        "📞 Chamadas"
        if st.session_state.sidebar_expandida
        else "📞"
    )
    label_relatorios = (
        "📈 Relatórios"
        if st.session_state.sidebar_expandida
        else "📈"
    )
    label_links = (
        "📑 Links úteis"
        if st.session_state.sidebar_expandida
        else "📑"
    )

    # ======================================================
    # BOTÃO VISÃO GERAL
    # ======================================================
    if st.button(
        label_visao,
        use_container_width=True,
        key="menu_visao"
    ):
        ir_para("visao_geral")

    # ======================================================
    # BOTÃO CHAMADAS
    # ======================================================
    if st.button(
        label_chamadas,
        use_container_width=True,
        key="menu_chamadas"
    ):
        ir_para("chamadas")

    # ======================================================
    # BOTÃO RELATÓRIOS
    # ======================================================
    if st.button(
        label_relatorios,
        use_container_width=True,
        key="menu_relatorios"
    ):
        ir_para("relatorios")

    # ======================================================
    # BOTÃO LINKS ÚTEIS
    # ======================================================
    if st.button(
        label_links,
        use_container_width=True,
        key="menu_links"
    ):
        ir_para("links")

# ==========================================================
# ROTEADOR PRINCIPAL
# ==========================================================

# ==========================================================
# VISÃO GERAL
# ==========================================================
if st.session_state.menu == "visao_geral":
    from modules import visao_geral
    visao_geral.render(
        st.session_state.refresh_rate
    )

# ==========================================================
# CHAMADAS
# ==========================================================
elif st.session_state.menu == "chamadas":
    if st.session_state.card is None:
        st.title("📞 Chamadas")
        st.caption(
            "Selecione um módulo para carregar"
        )
        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown("#### 🚫 Chamada Recusada")
            if st.button(
                "Abrir",
                key="card_recusada",
                use_container_width=True
            ):
                st.session_state.card = "recusada"
                st.rerun()

        with c2:
            st.markdown("#### 📊 Análise de Chamadas")
            job = st.session_state.jobs.get("analise_chamadas")
            if job and job["status"] == "running":
                st.caption(
                    f"🔄 Rodando em segundo plano "
                    f"({int(job['progresso'] * 100)}%)"
                )
            elif job and job["status"] == "done":
                st.caption("✅ Resultado pronto")
            if st.button(
                "Abrir",
                key="card_analise",
                use_container_width=True
            ):
                st.session_state.card = "analise"
                st.rerun()

        with c3:
            st.markdown("#### ☎️ Ligação por Ramal")
            if st.button(
                "Abrir",
                key="card_ramal",
                use_container_width=True
            ):
                st.session_state.card = "ramal"
                st.rerun()

    else:
        if st.button("← Voltar para os cards"):
            st.session_state.card = None
            st.rerun()

        if st.session_state.card == "analise":
            from modules import analise_chamadas_async
            analise_chamadas_async.render()
        elif st.session_state.card == "recusada":
            from modules import chamada_recusada
            chamada_recusada.render()
        elif st.session_state.card == "ramal":
            from modules import ligacao_ramal
            ligacao_ramal.render()

# ==========================================================
# MENU RELATÓRIOS
# ==========================================================
elif st.session_state.menu == "relatorios":
    st.title("📈 Relatórios")
    st.caption(
        "Área de relatórios do sistema - Selecione um relatório para visualizar"
    )
    from modules import relatorios
    relatorios.render()

# ==========================================================
# MENU LINKS ÚTEIS
# ==========================================================
elif st.session_state.menu == "links":
    st.title("📑 Links úteis")
    st.caption(
        "Links e recursos úteis do ServiceDesk"
    )
    from modules import links
    links.render()
