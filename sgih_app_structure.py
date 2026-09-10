# ==========================================
# ESTRUTURA MODULAR - SGIH COM MENU ESTILO PAINEL
# ==========================================
import streamlit as st

# Configuração da página (DEVE ser a primeira chamada)
st.set_page_config(
    page_title="SGIH - Sistema de Gestão Inteligente de ServiceDesk",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 1. ESTADO DA SESSÃO
# ==========================================
if "pagina_atual" not in st.session_state:
    st.session_state["pagina_atual"] = "Visão Geral"
if "modulo_ativo" not in st.session_state:
    st.session_state["modulo_ativo"] = None

def mudar_pagina(nome_pagina):
    st.session_state["pagina_atual"] = nome_pagina
    st.session_state["modulo_ativo"] = None

def abrir_modulo(nome_modulo):
    st.session_state["modulo_ativo"] = nome_modulo

# ==========================================
# 2. MENU LATERAL ESTILO PAINEL (IGUAL A FOTO)
# ==========================================
with st.sidebar:
    # ===== TÍTULO DO SISTEMA - CAIXA SUPERIOR =====
    st.markdown("""
        <div style="
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            padding: 18px;
            border-radius: 12px;
            margin-bottom: 20px;
            border: 1px solid #334155;
        ">
            <h2 style="color: #ffffff; margin: 0; font-size: 22px;">⚡ SGIH</h2>
            <p style="color: #94a3b8; font-size: 12px; margin: 6px 0 0 0;">Sistema de Gestão Inteligente de Helpdesk</p>
        </div>
    """, unsafe_allow_html=True)

    # ===== BLOCO DE NAVEGAÇÃO =====
    st.markdown("""
        <div style="
            background: #1e293b;
            padding: 16px;
            border-radius: 12px;
            margin-bottom: 16px;
            border: 1px solid #334155;
        ">
            <p style="color: #cbd5e1; font-size: 13px; margin: 0 0 12px 0; font-weight: 500;">📂 Navegação</p>
    """, unsafe_allow_html=True)

    # Botões com estilo visual unificado
    if st.button("📊 Visão Geral", use_container_width=True):
        mudar_pagina("Visão Geral")
    if st.button("📞 Chamadas", use_container_width=True):
        mudar_pagina("Chamadas")
    if st.button("👥 Técnicos", use_container_width=True):
        mudar_pagina("Técnicos")
    if st.button("📈 Relatórios", use_container_width=True):
        mudar_pagina("Relatórios")
    if st.button("📑 Links Úteis", use_container_width=True):
        mudar_pagina("Util")

    st.markdown("</div>", unsafe_allow_html=True)  # Fecha bloco Navegação

    # ===== BLOCO DE CONFIGURAÇÕES (com slider estilo Steps da foto) =====
    st.markdown("""
        <div style="
            background: #1e293b;
            padding: 16px;
            border-radius: 12px;
            border: 1px solid #334155;
        ">
            <p style="color: #cbd5e1; font-size: 13px; margin: 0 0 10px 0; font-weight: 500;">⚙️ Configurações</p>
        </div>
    """, unsafe_allow_html=True)

    # Slider estilo "Steps" da imagem
    refresh_rate = st.slider(
        "⏱️ Taxa de Atualização (segundos)",
        min_value=10,
        max_value=300,
        value=30,
        step=5
    )

    st.markdown("</div>", unsafe_allow_html=True)  # Fecha bloco Configurações

    # ===== RODAPÉ =====
    st.markdown("""
        <div style="
            margin-top: 16px;
            padding: 12px;
            text-align: center;
        ">
            <p style="color: #64748b; font-size: 11px; margin: 0;">v2.1.0 • Online ✅</p>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# 3. ROTEAMENTO DE PÁGINAS (mantive o seu funcionamento)
# ==========================================
pagina = st.session_state["pagina_atual"]
modulo = st.session_state["modulo_ativo"]

if pagina == "Visão Geral":
    st.title("📊 Visão Geral do Sistema")
    st.write("Acompanhamento em tempo real dos serviços essenciais (PABX, Kanban e WhatsApp).")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="PABX (Agentes Livres)", value="23 Livres", delta="17 Ocupados")
    with col2:
        st.metric(label="Kanban (Tarefas Abertas)", value="32", delta="5 Urgentes")
    with col3:
        st.metric(label="WhatsApp Status", value="Conectado", delta="API Online")
        
    st.markdown("---")
    st.subheader("Atalhos Rápidos de Módulos")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("🔴 Chamadas Recusadas", use_container_width=True):
            st.session_state["pagina_atual"] = "Chamadas"
            st.session_state["modulo_ativo"] = "Recusadas"
            st.rerun()
    with c2:
        if st.button("📋 Análise de Chamadas (CDR)", use_container_width=True):
            st.session_state["pagina_atual"] = "Chamadas"
            st.session_state["modulo_ativo"] = "Analise"
            st.rerun()
    with c3:
        if st.button("📞 Ligações por Ramal", use_container_width=True):
            st.session_state["pagina_atual"] = "Chamadas"
            st.session_state["modulo_ativo"] = "Ramal"
            st.rerun()

elif pagina == "Chamadas":
    st.title("📞 Módulo de Chamadas")
    
    if modulo is None:
        st.write("Selecione abaixo o subsistema de chamadas que deseja carregar:")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
                <div style="background: #1e293b; padding: 20px; border-radius: 8px; border-left: 5px solid #dc2626; height: 160px;">
                    <h4 style="color: white; margin-top:0;">Chamadas Recusadas</h4>
                    <p style="color: #94a3b8; font-size: 13px;">Visualize chamadas perdidas e recusadas por fila ou técnico.</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Abrir Módulo Recusadas", use_container_width=True):
                abrir_modulo("Recusadas")
                st.rerun()
                
        with col2:
            st.markdown("""
                <div style="background: #1e293b; padding: 20px; border-radius: 8px; border-left: 5px solid #3b82f6; height: 160px;">
                    <h4 style="color: white; margin-top:0;">Análise de Chamadas</h4>
                    <p style="color: #94a3b8; font-size: 13px;">Consultas detalhadas ao CDR, TMA e métricas de atendimento.</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Abrir Módulo Análise", use_container_width=True):
                abrir_modulo("Analise")
                st.rerun()
                
        with col3:
            st.markdown("""
                <div style="background: #1e293b; padding: 20px; border-radius: 8px; border-left: 5px solid #16a34a; height: 160px;">
                    <h4 style="color: white; margin-top:0;">Ligações por Ramal</h4>
                    <p style="color: #94a3b8; font-size: 13px;">Acompanhe o volume de tráfego telefônico por ramal específico.</p>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Abrir Módulo Ramal", use_container_width=True):
                abrir_modulo("Ramal")
                st.rerun()
    else:
        if st.button("← Voltar para os Cards de Chamadas"):
            st.session_state["modulo_ativo"] = None
            st.rerun()
        st.markdown("---")
        
        if modulo == "Recusadas":
            st.subheader("🔴 Módulo: Chamadas Recusadas / Abandonadas")
            st.info("Aqui entram as tabelas e requisições específicas de chamadas perdidas...")
        elif modulo == "Analise":
            st.subheader("📊 Módulo: Análise e Acompanhamento de Chamadas (CDR)")
            st.info("Aqui entra o código de login no PABX, pesquisa de data e gráficos pesados de CDR...")
        elif modulo == "Ramal":
            st.subheader("📞 Módulo: Ligações por Ramal")
            st.info("Aqui entram os filtros e relatórios segregados por ramal...")

elif pagina == "Técnicos":
    st.title("👥 Gestão de Técnicos")
    st.write("Monitoramento detalhado da equipe técnica e status no WhatsApp / PABX.")

elif pagina == "Relatórios":
    st.title("📈 Relatórios Consolidados")
    st.write("Geração de relatórios gerenciais sob demanda.")

elif pagina == "Util":
    st.title("📑 Links Úteis")
    st.write("Links úteis para gerenciamento e Monitoramento de Tarefas.")
