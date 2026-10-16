"""
Módulo: Visão Geral do SGIH
===========================
Monitoramento do PABX, Kanban e WhatsApp.
O PABX utiliza autenticação HTTP com CSRF e consulta
a tabela real de agentes.
Kanban e WhatsApp agora usam consulta real.
"""
import json
import os
import re
import time
import unicodedata
import requests
import streamlit as st
from bs4 import BeautifulSoup

# ============================================================
# CONFIGURAÇÕES DO PABX
# ============================================================
LOGIN_URL = "https://pabx.evence.com.br/login"
MONITOR_URL = (
    "https://pabx.evence.com.br/"
    "callcenter/monitoramentoAgentes/detalhes"
    "?agentes=46,47,49,50,52,53"
)
REQUEST_TIMEOUT = 15
CACHE_TTL = 30

# ============================================================
# CONFIGURAÇÕES DO KANBAN
# ============================================================
KANBAN_LOGIN_URL = "https://kanban.interativanet.com.br/?controller=AuthController&action=check"
KANBAN_URL = (
    "https://kanban.interativanet.com.br/"
    "?controller=ProjectOverviewController&action=show"
    "&project_id=1&search=status%3Aopen"
)
TAREFAS_FILE = "tarefas_pendentes.json"

# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================
def remover_acentos(texto):
    """Remove acentos e converte o texto para minúsculas."""
    texto = str(texto or "")
    return (
        unicodedata.normalize("NFKD", texto)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
        .strip()
    )


def normalizar_status(texto):
    """
    Converte o status recebido do PABX para:
    livre, ocupado, pausa ou offline.
    """
    texto = remover_acentos(texto)
    if any(p in texto for p in (
        "indisponivel",
        "offline",
        "desconectado",
        "deslogado",
    )):
        return "offline"
    if "pausa" in texto:
        return "pausa"
    if any(p in texto for p in (
        "ocupado",
        "falando",
        "em ligacao",
        "em chamada",
        "atendimento",
    )):
        return "ocupado"
    if "livre" in texto or "disponivel" in texto:
        return "livre"
    # Não presumir que um status desconhecido seja livre.
    return "offline"


# ============================================================
# SISTEMA DE ÁUDIO
# ============================================================
def renderizar_botao_audio():
    audio_url = "https://notificationsounds.com/storage/sounds/file-sounds-1150-pristine.mp3"
    tocar_agora = "true" if st.session_state.get("play_alert", False) else "false"

    sound_html = f"""
    <div style="display: flex; justify-content: flex-end; align-items: center; height: 40px;">
        <button id="btn-ativar-som" onclick="testarEAtivarSom()" style="
            background:#2563eb;
            color:white;
            border:none;
            border-radius:8px;
            height:40px;
            font-weight:600;
            padding:0 18px;
            cursor:pointer;
        ">🔊 Ativar & Testar Som</button>
    </div>
    <audio id="notif-sound" src="{audio_url}" preload="auto"></audio>
    <script>
        var audio = document.getElementById('notif-sound');
        var deveTocarAutomatico = {tocar_agora};
        function testarEAtivarSom() {{
            if (audio) {{
                audio.volume = 1.0;
                audio.play()
                    .then(function() {{
                        alert("✅ Excelente! Som do painel ativado e autorizado com sucesso.");
                    }})
                    .catch(function(err) {{
                        alert("❌ Erro ao ativar o som. Verifique se o volume do computador está ligado.");
                    }});
            }}
        }}
        if (deveTocarAutomatico && audio) {{
            audio.volume = 1.0;
            audio.play().catch(function(e) {{
                console.log("Autoplay bloqueado pelo navegador.");
            }});
        }}
    </script>
    """
    st.components.v1.html(sound_html, height=50)

    # Reseta o flag após tentar tocar
    if st.session_state.get("play_alert", False):
        st.session_state.play_alert = False


# ============================================================
# PERSISTÊNCIA DAS TAREFAS DO KANBAN
# ============================================================
def carregar_tarefas_salvas():
    if os.path.exists(TAREFAS_FILE):
        try:
            with open(TAREFAS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def salvar_tarefas(tarefas):
    with open(TAREFAS_FILE, "w", encoding="utf-8") as f:
        json.dump(tarefas, f, indent=4, ensure_ascii=False)


# ============================================================
# LOGIN NO PABX
# ============================================================
def login():
    """
    Autentica no PABX usando EMAIL e SENHA do st.secrets.
    Retorna:
        (sessao, None) se o login aparentar sucesso.
        (None, mensagem) em caso de erro.
    """
    session = requests.Session()
    try:
        # Credenciais configuradas no Streamlit.
        email = st.secrets["EMAIL"]
        senha = st.secrets["SENHA"]
        # Identifica o cliente HTTP.
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })
        # Abre a página de login para obter o CSRF.
        resposta = session.get(
            LOGIN_URL,
            timeout=REQUEST_TIMEOUT,
        )
        resposta.raise_for_status()
        soup = BeautifulSoup(resposta.text, "html.parser")
        campo_token = soup.find(
            "input",
            {"name": "_token"},
        )
        if campo_token is None or not campo_token.get("value"):
            session.close()
            return None, (
                "O PABX não retornou o token CSRF. "
                "Verifique a página de login."
            )
        token = campo_token["value"]
        # Dados enviados ao formulário de autenticação.
        payload = {
            "login": email,
            "senha": senha,
            "_token": token,
        }
        resposta_login = session.post(
            LOGIN_URL,
            data=payload,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        resposta_login.raise_for_status()
        # Verificação básica para detectar se continuamos
        # na página de login depois do envio do formulário.
        url_final = resposta_login.url.rstrip("/")
        pagina_final = BeautifulSoup(
            resposta_login.text,
            "html.parser",
        )
        campo_login = pagina_final.find(
            "input",
            {"name": "_token"},
        )
        ainda_no_login = (
            url_final == LOGIN_URL.rstrip("/")
            and campo_login is not None
        )
        if ainda_no_login:
            session.close()
            return None, (
                "Falha de autenticação no PABX. "
                "Confira as credenciais."
            )
        return session, None
    except KeyError:
        session.close()
        return None, (
            "Configure EMAIL e SENHA em "
            ".streamlit/secrets.toml."
        )
    except requests.Timeout:
        session.close()
        return None, "Tempo limite excedido no login do PABX."
    except requests.RequestException:
        session.close()
        return None, "Falha de conexão durante o login no PABX."
    except Exception:
        session.close()
        return None, "Erro inesperado durante o login no PABX."


# ============================================================
# CONSULTA DOS AGENTES
# ============================================================
def get_agentes(session):
    """
    Consulta a página de monitoramento dos técnicos.
    A lógica fornecida utiliza:
        Coluna 0: nome do técnico.
        Coluna 2: status do técnico.
    Retorna uma lista de tuplas:
        [("Leonardo", "livre"), ("Matheus", "pausa")]
    """
    resposta = session.get(
        MONITOR_URL,
        timeout=REQUEST_TIMEOUT,
    )
    resposta.raise_for_status()
    soup = BeautifulSoup(resposta.text, "html.parser")
    tabela = soup.find("table")
    if tabela is None:
        raise ValueError(
            "Tabela de agentes não encontrada. "
            "Verifique a sessão ou o HTML do PABX."
        )
    agentes = []
    for linha in tabela.find_all("tr"):
        colunas = linha.find_all("td")
        # Ignora cabeçalhos e linhas incompletas.
        if len(colunas) < 3:
            continue
        # Extrai o nome.
        nome = colunas[0].get_text(" ", strip=True)
        # Remove o texto auxiliar que pode aparecer no nome.
        nome = re.split(
            r"Última chamada",
            nome,
            flags=re.IGNORECASE,
        )[0].strip()
        # Extrai o texto da terceira coluna.
        texto_status = colunas[2].get_text(
            " ",
            strip=True,
        )
        if not nome:
            continue
        status = normalizar_status(texto_status)
        agentes.append((nome, status))
    return agentes


# ============================================================
# CONSULTA PABX COM CACHE
# ============================================================
@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def _status_pabx_cache(ttl_marker):
    """
    Armazena temporariamente os dados do PABX.
    ttl_marker integra a chave do cache, permitindo renovar
    a consulta quando o intervalo de atualização muda.
    """
    _ = ttl_marker
    session, erro = login()
    if session is None:
        return {
            "ok": False,
            "agentes": [],
            "erro": erro,
        }
    try:
        agentes = get_agentes(session)
        return {
            "ok": True,
            "agentes": agentes,
            "erro": None,
        }
    except requests.Timeout:
        return {
            "ok": False,
            "agentes": [],
            "erro": "Tempo limite excedido na consulta do PABX.",
        }
    except requests.RequestException:
        return {
            "ok": False,
            "agentes": [],
            "erro": "Falha de conexão ao consultar os técnicos.",
        }
    except ValueError as erro:
        return {
            "ok": False,
            "agentes": [],
            "erro": str(erro),
        }
    except Exception:
        return {
            "ok": False,
            "agentes": [],
            "erro": "Erro inesperado ao consultar os técnicos.",
        }
    finally:
        session.close()


# ============================================================
# KANBAN — LOGIN E ATUALIZAÇÃO
# ============================================================
def login_kanban():
    session = requests.Session()
    try:
        r = session.get(
            "https://kanban.interativanet.com.br/?controller=AuthController&action=login",
            timeout=REQUEST_TIMEOUT,
        )
        soup = BeautifulSoup(r.text, "html.parser")
        csrf_token = soup.find("input", {"name": "csrf_token"})

        payload = {
            "username": st.secrets["KANBAN_USER"],
            "password": st.secrets["KANBAN_PASS"],
        }
        if csrf_token:
            payload["csrf_token"] = csrf_token["value"]

        session.post(KANBAN_LOGIN_URL, data=payload, timeout=REQUEST_TIMEOUT)
        return session
    except Exception:
        return None


def atualizar_kanban(session_kb):
    """
    Sincroniza com o Kanban sem duplicar tarefas.
    Dispara som quando detecta nova tarefa criada.
    """
    if not session_kb:
        return

    try:
        r = session_kb.get(KANBAN_URL, timeout=REQUEST_TIMEOUT)
        soup = BeautifulSoup(r.text, "html.parser")
        atividades = soup.find_all("div", class_="activity-content")

        tarefas_atuais = st.session_state.tarefas_kanban.copy()
        houve_alteracao = False
        disparar_som = False

        for atividade in reversed(atividades):
            title_p = atividade.find("p", class_="activity-title")
            if not title_p:
                continue

            texto_acao = title_p.get_text(" ", strip=True)
            link_task = title_p.find("a")
            date_span = title_p.find("small", class_="activity-date")

            if not link_task or not date_span:
                continue

            task_id = link_task.get_text(strip=True)
            data_atividade = date_span.get_text(strip=True)

            desc_div = atividade.find("div", class_="activity-description")
            titulo_tarefa = (
                desc_div.find("p", class_="activity-task-title").get_text(strip=True)
                if desc_div
                else "Sem título"
            )

            if "criou a tarefa" in texto_acao:
                if task_id not in tarefas_atuais:
                    tarefas_atuais[task_id] = {
                        "titulo": titulo_tarefa,
                        "data_criacao": data_atividade,
                        "status": "Pendente",
                    }
                    houve_alteracao = True
                    disparar_som = True
            elif "finalizou a tarefa" in texto_acao:
                if task_id in tarefas_atuais:
                    del tarefas_atuais[task_id]
                    houve_alteracao = True

        if houve_alteracao:
            st.session_state.tarefas_kanban = tarefas_atuais
            salvar_tarefas(tarefas_atuais)
            if disparar_som:
                st.session_state.play_alert = True

    except Exception as e:
        st.sidebar.error(f"Erro ao ler Kanban: {e}")


# ============================================================
# WHATSFLUX — STATUS ONLINE
# ============================================================
def login_e_get_status_whatsflux():
    login_api_url = "https://api.whatsflux.com.br/auth/login"
    users_api_url = "https://api.whatsflux.com.br/users"

    session = requests.Session()
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "Referer": "https://app.whatsflux.com.br/login",
        "Origin": "https://app.whatsflux.com.br",
    }
    session.headers.update(headers)

    tecnicos_alvo = ["Leonardo", "Matheus", "Gabriel", "Ramon", "Thiago", "Vinicius"]
    status_tecnicos = {nome: "offline" for nome in tecnicos_alvo}

    try:
        email_whats = st.secrets["WHATSFLUX_EMAIL"]
        senha_whats = st.secrets["WHATSFLUX_SENHA"]
    except KeyError:
        return "Configure o Secrets (WHATSFLUX_EMAIL / WHATSFLUX_SENHA)", {}

    try:
        payload = {"email": email_whats, "password": senha_whats}
        res_login = session.post(login_api_url, json=payload, timeout=10)

        if res_login.status_code not in [200, 201, 302]:
            return f"Falha Auth (HTTP {res_login.status_code})", {}

        dados_resposta = res_login.json()
        token = dados_resposta.get("token") or dados_resposta.get("access_token")
        if token:
            session.headers.update({"Authorization": f"Bearer {token}"})

        res_users = session.get(users_api_url, timeout=10)
        if res_users.status_code != 200:
            return f"Erro API Users ({res_users.status_code})", {}

        resposta_json = res_users.json()
        dados_usuarios = resposta_json.get("users", [])

        def normalizar(texto):
            if not texto:
                return ""
            return (
                unicodedata.normalize("NFKD", texto)
                .encode("ASCII", "ignore")
                .decode("ASCII")
                .lower()
                .strip()
            )

        for usuario in dados_usuarios:
            nome_usuario = usuario.get("name", "")
            is_online = usuario.get("online", False)
            nome_usuario_limpo = normalizar(nome_usuario)

            for tecnico in tecnicos_alvo:
                tecnico_limpo = normalizar(tecnico)
                if tecnico_limpo in nome_usuario_limpo and is_online:
                    status_tecnicos[tecnico] = "online"

        return "OK", status_tecnicos
    except Exception as e:
        return f"Erro de Conexão ({str(e)[:30]})", {}


# ============================================================
# INTERFACE DA VISÃO GERAL
# ============================================================
def render(refresh_rate=30):
    """
    Renderiza o painel de monitoramento.
    """
    refresh_rate = max(5, min(300, int(refresh_rate)))

    # Inicialização de estados
    if "tarefas_kanban" not in st.session_state:
        st.session_state.tarefas_kanban = carregar_tarefas_salvas()
    if "play_alert" not in st.session_state:
        st.session_state.play_alert = False
    if "session_kanban" not in st.session_state:
        st.session_state.session_kanban = None

    @st.fragment(run_every=refresh_rate)
    def painel_monitoramento():
        # Cabeçalho original do SGIH.
        st.title("Visão Geral")
        st.caption(
            "Monitoramento do ambiente e ferramentas - Service Desk"
        )

        
        # Muda a chave de consulta a cada intervalo.
        ttl_marker = int(time.time() // refresh_rate)
        resultado_pabx = _status_pabx_cache(ttl_marker)

        # ---------- KANBAN (real) ----------
        if st.session_state.session_kanban is None:
            st.session_state.session_kanban = login_kanban()
        atualizar_kanban(st.session_state.session_kanban)
        tarefas_kanban = st.session_state.tarefas_kanban

        # ---------- WHATSFLUX (real) ----------
        status_whats, whatsapp = login_e_get_status_whatsflux()

        # Layout de três colunas.
        col1, col2, col3 = st.columns(
            [1.3, 1.7, 1],
            gap="medium",
        )

        # ----------------------------------------------------
        # COLUNA 1 — PABX
        # ----------------------------------------------------
        with col1:
            st.subheader("☎️ Status PABX")
            if not resultado_pabx["ok"]:
                st.error(resultado_pabx["erro"])
            else:
                agentes = resultado_pabx["agentes"]
                if not agentes:
                    st.warning(
                        "Nenhum técnico encontrado na tabela "
                        "retornada pelo PABX."
                    )
                else:
                    livres = sum(status == "livre" for _, status in agentes)
                    ocupados = sum(status == "ocupado" for _, status in agentes)
                    pausas = sum(status == "pausa" for _, status in agentes)
                    offline = sum(status == "offline" for _, status in agentes)

                    st.markdown(
                        f"""
                        <div style="
                            white-space: nowrap;
                            width: 50px;
                            max-width: 50px;
                            font-size: 12px;
                            padding: 6px 0;
                            line-height: 1.5;
                            margin-bottom: 10px;
                        ">
                            🟢 {livres} livres
                            &nbsp;|&nbsp;
                            🔴 {ocupados} ocupados
                            &nbsp;|&nbsp;
                            🟡 {pausas} em pausa
                            &nbsp;|&nbsp;
                            ⚪ {offline} offline
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    for nome, status in agentes:
                        if status == "offline":
                            continue
                        cor = {
                            "livre": "🟢",
                            "ocupado": "🔴",
                            "pausa": "🟡",
                            "offline": "⚪",
                        }.get(status, "⚪")
                        st.write(f"{cor} {nome} — {status}")

        # ----------------------------------------------------
        # COLUNA 2 — KANBAN
        # ----------------------------------------------------
        with col2:
            st.subheader("🗂️ Tarefas Kanban")
            if not tarefas_kanban:
                st.info("Nenhuma tarefa pendente.")
            else:
                for task_id, tarefa in tarefas_kanban.items():
                    st.write(
                        f"• {tarefa['titulo']} "
                        f"({tarefa.get('status', 'Pendente')})"
                    )

        # ----------------------------------------------------
        # COLUNA 3 — WHATSAPP (WhatsFlux)
        # ----------------------------------------------------
        with col3:
            st.subheader("💬 WhatsApp")
            if status_whats != "OK":
                st.warning(status_whats)
            else:
                for nome, status in whatsapp.items():
                    cor = "🟢" if status == "online" else "⚪"
                    st.write(f"{cor} {nome} — {status}")

    # Executa o painel com atualização automática.
    painel_monitoramento()
