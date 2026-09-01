"""
Estrutura Modular e Unificada - SGIH (Sistema de Gestão Inteligente de Helpdesk)
Este arquivo demonstra como estruturar o aplicativo Streamlit em um sistema único,
utilizando controle de estado para navegação no menu lateral e carregamento sob demanda (lazy loading)
dos módulos pesados (como Análise de Chamadas, Chamadas Recusadas e Ligações por Ramal).
"""

import streamlit as st

# Configuração da página (deve ser a primeira chamada Streamlit)
st.set_page_config(
    page_title="SGIH - Sistema de Gestão Inteligente de ServiceDesk",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================================
# 1. ESTADO DA SESSÃO PARA NAVEGAÇÃO E MÓDULOS
# ==========================================
if "pagina_atual" not in st.session_state:
    st.session_state["pagina_atual"] = "Visão Geral"

if "modulo_ativo" not in st.session_state:
    st.session_state["modulo_ativo"] = None

def mudar_pagina(nome_pagina):
    st.session_state["pagina_atual"] = nome_pagina
    st.session_state["modulo_ativo"] = None # Reseta o módulo interno ao trocar de menu

def abrir_modulo(nome_modulo):
    st.session_state["modulo_ativo"] = nome_modulo

# ==========================================
# 2. MENU LATERAL PERSONALIZADO (SGIH)
# ==========================================
with st.sidebar:
    st.markdown("""
        <div style="padding: 10px 0 20px 0; border-bottom: 1px solid #334155; margin-bottom: 20px;">
            <h2 style="color: #ffffff; margin: 0; font-size: 24px;">⚡ SGIH</h2>
            <p style="color: #94a3b8; font-size: 12px; margin: 4px 0 0 0;">Sistema de Gestão Inteligente de ServiceDesk</p>
        </div>
    """, unsafe_allow_html=True)
   
    # Botões do menu lateral
    if st.button("📊 Visão Geral", use_container_width=True):
        mudar_pagina("Visão Geral")
    
    if st.button("📞 Chamadas", use_container_width=True):
        mudar_pagina("Chamadas")
        
    if st.button("👥 Técnicos", use_container_width=True):
        mudar_pagina("Técnicos")
        
    if st.button("📈 Relatórios", use_container_width=True):
        mudar_pagina("Relatórios")

    if st.button("📑 Link Util", use_container_width=True):
        mudar_pagina("Util")

    st.markdown("---")
    st.markdown("### Configurações")
    refresh_rate = st.slider("Atualização (segundos)", 10, 300, 30, 5)

# ==========================================
# 3. ROTEAMENTO DE PÁGINAS E LAZY LOADING
# ==========================================

pagina = st.session_state["pagina_atual"]
modulo = st.session_state["modulo_ativo"]

if pagina == "Visão Geral":
    st.title("📊 Visão Geral do Sistema")
    st.write("Acompanhamento em tempo real dos serviços essenciais (PABX, Kanban e WhatsApp).")
    
    # Carregamento leve inicial (Apenas status rápido)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="PABX (Agentes Livres)", value="23 Livres", delta="17 Ocupados")
    with col2:
        st.metric(label="Kanban (Tarefas Abertas)", value="32", delta="5 Urgentes")
    with col3:
        st.metric(label="WhatsApp Status", value="Conectado", delta="API Online")
        
    st.markdown("---")
    st.subheader("Atalhos Rápidos de Módulos")
    
    # Cards interativos na visão geral que direcionam para os módulos
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
    
    # Se nenhum módulo interno estiver selecionado, exibe os cards de escolha
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
        # Botão para voltar à seleção de cards do módulo
        if st.button("← Voltar para os Cards de Chamadas"):
            st.session_state["modulo_ativo"] = None
            st.rerun()
            
        st.markdown("---")
        
        # LAZY LOADING: O código pesado de cada módulo só executa aqui quando aberto!
        if modulo == "Recusadas":
            st.subheader("🔴 Módulo: Chamadas Recusadas / Abandonadas")
            st.info("Aqui entram as tabelas e requisições específicas de chamadas perdidas...")
            # Exemplo de tabela leve ou carregamento de dados sob demanda
            
        elif modulo == "Analise":
            st.subheader("📊 Módulo: Análise e Acompanhamento de Chamadas (CDR)")
            st.info("Aqui entra o código de login no PABX, pesquisa de data e gráficos pesados de CDR...")
            # Chamada da função buscar_cdr() apenas neste momento!
            
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
    st.title("📑 Links Uteis")
    st.write("Geração de relatórios gerenciais sob demanda.")



