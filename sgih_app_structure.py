import express, { Request, Response } from 'express';
import * as cheerio from 'cheerio';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import dotenv from 'dotenv';

dotenv.config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

// Path to tarefas_pendentes.json
const TAREFAS_FILE = path.join(__dirname, 'tarefas_pendentes.json');
const PYTHON_FILE = path.join(__dirname, 'sgih_monitoramento.py');

// In-memory or env credentials store (mirroring st.secrets)
let secretsStore = {
  EMAIL: process.env.EMAIL || '',
  SENHA: process.env.SENHA || '',
  KANBAN_USER: process.env.KANBAN_USER || '',
  KANBAN_PASS: process.env.KANBAN_PASS || '',
  WHATSFLUX_EMAIL: process.env.WHATSFLUX_EMAIL || '',
  WHATSFLUX_SENHA: process.env.WHATSFLUX_SENHA || '',
};

// Simulation / Mock switch for offline/demo testing
let demoMode = true; // Enabled by default if secrets are empty, allows testing
let pendingAlert = false;

// ------------------------------------------------------------
// PERSISTÊNCIA DAS TAREFAS DO KANBAN
// ------------------------------------------------------------
function carregarTarefasSalvas(): Record<string, { titulo: string; data_criacao: string; status: string }> {
  if (fs.existsSync(TAREFAS_FILE)) {
    try {
      const data = fs.readFileSync(TAREFAS_FILE, 'utf-8');
      return JSON.parse(data);
    } catch {
      return {};
    }
  }
  return {};
}

function salvarTarefas(tarefas: Record<string, { titulo: string; data_criacao: string; status: string }>) {
  try {
    fs.writeFileSync(TAREFAS_FILE, JSON.stringify(tarefas, null, 2), 'utf-8');
  } catch (err) {
    console.error('Erro ao salvar tarefas:', err);
  }
}

// ------------------------------------------------------------
// FUNÇÕES AUXILIARES (EXATAS DO PYTHON)
// ------------------------------------------------------------
function removerAcentos(texto: string): string {
  return String(texto || '')
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

function normalizarStatus(texto: string): 'livre' | 'ocupado' | 'pausa' | 'offline' {
  const norm = removerAcentos(texto);
  if (
    norm.includes('indisponivel') ||
    norm.includes('offline') ||
    norm.includes('desconectado') ||
    norm.includes('deslogado')
  ) {
    return 'offline';
  }
  if (norm.includes('pausa')) {
    return 'pausa';
  }
  if (
    norm.includes('ocupado') ||
    norm.includes('falando') ||
    norm.includes('em ligacao') ||
    norm.includes('em chamada') ||
    norm.includes('atendimento')
  ) {
    return 'ocupado';
  }
  if (norm.includes('livre') || norm.includes('disponivel')) {
    return 'livre';
  }
  return 'offline';
}

// ------------------------------------------------------------
// PABX
// ------------------------------------------------------------
const PABX_LOGIN_URL = 'https://pabx.evence.com.br/login';
const PABX_MONITOR_URL = 'https://pabx.evence.com.br/callcenter/monitoramentoAgentes/detalhes?agentes=46,47,49,50,52,53';

async function fetchPabx(secrets: typeof secretsStore) {
  if (!secrets.EMAIL || !secrets.SENHA) {
    if (demoMode) {
      // Demo simulated real-time agents
      return {
        ok: true,
        agentes: [
          ['Leonardo Silva', 'livre'],
          ['Matheus Oliveira', 'ocupado'],
          ['Gabriel Costa', 'pausa'],
          ['Ramon Souza', 'livre'],
          ['Thiago Rocha', 'offline'],
          ['Vinicius Ferreira', 'ocupado'],
        ] as [string, string][],
        erro: null,
        isDemo: true,
      };
    }
    return {
      ok: false,
      agentes: [],
      erro: 'Configure EMAIL e SENHA em .streamlit/secrets.toml.',
      isDemo: false,
    };
  }

  try {
    const cookies: string[] = [];

    // Step 1: GET login page to get CSRF token
    const resGet = await fetch(PABX_LOGIN_URL, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      },
    });

    const setCookies = resGet.headers.get('set-cookie');
    if (setCookies) {
      cookies.push(...setCookies.split(',').map((c) => c.split(';')[0].trim()));
    }

    const htmlGet = await resGet.text();
    const $get = cheerio.load(htmlGet);
    const csrfToken = $get('input[name="_token"]').attr('value');

    if (!csrfToken) {
      return {
        ok: false,
        agentes: [],
        erro: 'O PABX não retornou o token CSRF. Verifique a página de login.',
      };
    }

    // Step 2: POST login form
    const bodyParams = new URLSearchParams();
    bodyParams.append('login', secrets.EMAIL);
    bodyParams.append('senha', secrets.SENHA);
    bodyParams.append('_token', csrfToken);

    const resLogin = await fetch(PABX_LOGIN_URL, {
      method: 'POST',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        Cookie: cookies.join('; '),
      },
      body: bodyParams.toString(),
      redirect: 'follow',
    });

    const loginSetCookies = resLogin.headers.get('set-cookie');
    if (loginSetCookies) {
      cookies.push(...loginSetCookies.split(',').map((c) => c.split(';')[0].trim()));
    }

    const htmlLogin = await resLogin.text();
    const $login = cheerio.load(htmlLogin);
    if ($login('input[name="_token"]').length > 0 && resLogin.url.includes('/login')) {
      return {
        ok: false,
        agentes: [],
        erro: 'Falha de autenticação no PABX. Confira as credenciais.',
      };
    }

    // Step 3: GET Monitor URL
    const resMonitor = await fetch(PABX_MONITOR_URL, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        Cookie: cookies.join('; '),
      },
    });

    const htmlMonitor = await resMonitor.text();
    const $mon = cheerio.load(htmlMonitor);
    const table = $mon('table');
    if (table.length === 0) {
      return {
        ok: false,
        agentes: [],
        erro: 'Tabela de agentes não encontrada. Verifique a sessão ou o HTML do PABX.',
      };
    }

    const agentes: [string, string][] = [];
    table.find('tr').each((_, row) => {
      const cols = $mon(row).find('td');
      if (cols.length < 3) return;

      let nome = cols.eq(0).text().replace(/\s+/g, ' ').trim();
      nome = nome.split(/Última chamada/i)[0].trim();
      const statusRaw = cols.eq(2).text().replace(/\s+/g, ' ').trim();

      if (nome) {
        agentes.push([nome, normalizarStatus(statusRaw)]);
      }
    });

    return { ok: true, agentes, erro: null };
  } catch (err: any) {
    if (demoMode) {
      return {
        ok: true,
        agentes: [
          ['Leonardo Silva', 'livre'],
          ['Matheus Oliveira', 'ocupado'],
          ['Gabriel Costa', 'pausa'],
          ['Ramon Souza', 'livre'],
          ['Thiago Rocha', 'offline'],
          ['Vinicius Ferreira', 'ocupado'],
        ] as [string, string][],
        erro: null,
        isDemo: true,
      };
    }
    return {
      ok: false,
      agentes: [],
      erro: `Falha de conexão durante o login no PABX (${err?.message || 'timeout'})`,
    };
  }
}

// ------------------------------------------------------------
// KANBAN
// ------------------------------------------------------------
const KANBAN_LOGIN_URL = 'https://kanban.interativanet.com.br/?controller=AuthController&action=check';
const KANBAN_URL = 'https://kanban.interativanet.com.br/?controller=ProjectOverviewController&action=show&project_id=1&search=status%3Aopen';

async function fetchKanban(secrets: typeof secretsStore) {
  let tarefas = carregarTarefasSalvas();
  let dispararSom = false;

  if (!secrets.KANBAN_USER || !secrets.KANBAN_PASS) {
    if (pendingAlert) {
      dispararSom = true;
      pendingAlert = false;
    }
    return {
      ok: true,
      tarefas,
      dispararSom,
      isDemo: demoMode,
    };
  }

  try {
    const cookies: string[] = [];
    const resLoginGet = await fetch('https://kanban.interativanet.com.br/?controller=AuthController&action=login');
    const setCookies = resLoginGet.headers.get('set-cookie');
    if (setCookies) {
      cookies.push(...setCookies.split(',').map((c) => c.split(';')[0].trim()));
    }
    const htmlLogin = await resLoginGet.text();
    const $login = cheerio.load(htmlLogin);
    const csrfToken = $login('input[name="csrf_token"]').attr('value') || '';

    const bodyParams = new URLSearchParams();
    bodyParams.append('username', secrets.KANBAN_USER);
    bodyParams.append('password', secrets.KANBAN_PASS);
    if (csrfToken) bodyParams.append('csrf_token', csrfToken);

    await fetch(KANBAN_LOGIN_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        Cookie: cookies.join('; '),
      },
      body: bodyParams.toString(),
    });

    const resOverview = await fetch(KANBAN_URL, {
      headers: {
        Cookie: cookies.join('; '),
      },
    });

    const htmlOverview = await resOverview.text();
    const $ov = cheerio.load(htmlOverview);
    const atividades = $ov('div.activity-content');

    let houveAlteracao = false;
    const tarefasAtuais = { ...tarefas };

    atividades.toArray().reverse().forEach((el) => {
      const $act = $ov(el);
      const titleP = $act.find('p.activity-title');
      if (!titleP.length) return;

      const textoAcao = titleP.text().replace(/\s+/g, ' ').trim();
      const linkTask = titleP.find('a');
      const dateSpan = titleP.find('small.activity-date');

      if (!linkTask.length || !dateSpan.length) return;

      const taskId = linkTask.text().trim();
      const dataAtividade = dateSpan.text().trim();

      const descDiv = $act.find('div.activity-description');
      const tituloTarefa = descDiv.find('p.activity-task-title').text().trim() || 'Sem título';

      if (textoAcao.includes('criou a tarefa')) {
        if (!tarefasAtuais[taskId]) {
          tarefasAtuais[taskId] = {
            titulo: tituloTarefa,
            data_criacao: dataAtividade,
            status: 'Pendente',
          };
          houveAlteracao = true;
          dispararSom = true;
        }
      } else if (textoAcao.includes('finalizou a tarefa')) {
        if (tarefasAtuais[taskId]) {
          delete tarefasAtuais[taskId];
          houveAlteracao = true;
        }
      }
    });

    if (houveAlteracao) {
      tarefas = tarefasAtuais;
      salvarTarefas(tarefas);
    }

    if (pendingAlert) {
      dispararSom = true;
      pendingAlert = false;
    }

    return {
      ok: true,
      tarefas,
      dispararSom,
      isDemo: false,
    };
  } catch (err: any) {
    if (pendingAlert) {
      dispararSom = true;
      pendingAlert = false;
    }
    return {
      ok: true,
      tarefas,
      dispararSom,
      erro: `Erro ao ler Kanban: ${err?.message || ''}`,
      isDemo: demoMode,
    };
  }
}

// ------------------------------------------------------------
// WHATSFLUX (WHATSAPP)
// ------------------------------------------------------------
const tecnicosAlvo = ['Leonardo', 'Matheus', 'Gabriel', 'Ramon', 'Thiago', 'Vinicius'];

async function fetchWhatsFlux(secrets: typeof secretsStore) {
  const statusTecnicos: Record<string, 'online' | 'offline'> = {};
  tecnicosAlvo.forEach((nome) => {
    statusTecnicos[nome] = 'offline';
  });

  if (!secrets.WHATSFLUX_EMAIL || !secrets.WHATSFLUX_SENHA) {
    if (demoMode) {
      // Demo active status
      statusTecnicos['Leonardo'] = 'online';
      statusTecnicos['Matheus'] = 'online';
      statusTecnicos['Gabriel'] = 'online';
      statusTecnicos['Ramon'] = 'offline';
      statusTecnicos['Thiago'] = 'online';
      statusTecnicos['Vinicius'] = 'offline';
      return {
        status: 'OK',
        whatsapp: statusTecnicos,
        isDemo: true,
      };
    }
    return {
      status: 'Configure o Secrets (WHATSFLUX_EMAIL / WHATSFLUX_SENHA)',
      whatsapp: {},
      isDemo: false,
    };
  }

  try {
    const loginRes = await fetch('https://api.whatsflux.com.br/auth/login', {
      method: 'POST',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        Accept: 'application/json, text/plain, */*',
        'Content-Type': 'application/json;charset=UTF-8',
        Referer: 'https://app.whatsflux.com.br/login',
        Origin: 'https://app.whatsflux.com.br',
      },
      body: JSON.stringify({
        email: secrets.WHATSFLUX_EMAIL,
        password: secrets.WHATSFLUX_SENHA,
      }),
    });

    if (![200, 201, 302].includes(loginRes.status)) {
      return {
        status: `Falha Auth (HTTP ${loginRes.status})`,
        whatsapp: {},
      };
    }

    const authData = (await loginRes.json()) as any;
    const token = authData?.token || authData?.access_token;
    if (!token) {
      return {
        status: 'Falha Auth (Token não encontrado)',
        whatsapp: {},
      };
    }

    const usersRes = await fetch('https://api.whatsflux.com.br/users', {
      headers: {
        Authorization: `Bearer ${token}`,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      },
    });

    if (usersRes.status !== 200) {
      return {
        status: `Erro API Users (${usersRes.status})`,
        whatsapp: {},
      };
    }

    const usersData = (await usersRes.json()) as any;
    const dadosUsuarios = usersData?.users || [];

    for (const usuario of dadosUsuarios) {
      const nomeUsuario = usuario?.name || '';
      const isOnline = Boolean(usuario?.online);
      const nomeUsuarioLimpo = removerAcentos(nomeUsuario);

      for (const tecnico of tecnicosAlvo) {
        const tecnicoLimpo = removerAcentos(tecnico);
        if (nomeUsuarioLimpo.includes(tecnicoLimpo) && isOnline) {
          statusTecnicos[tecnico] = 'online';
        }
      }
    }

    return {
      status: 'OK',
      whatsapp: statusTecnicos,
    };
  } catch (err: any) {
    if (demoMode) {
      statusTecnicos['Leonardo'] = 'online';
      statusTecnicos['Matheus'] = 'online';
      statusTecnicos['Gabriel'] = 'online';
      statusTecnicos['Ramon'] = 'offline';
      statusTecnicos['Thiago'] = 'online';
      statusTecnicos['Vinicius'] = 'offline';
      return {
        status: 'OK',
        whatsapp: statusTecnicos,
        isDemo: true,
      };
    }
    return {
      status: `Erro de Conexão (${String(err?.message || 'falha').slice(0, 30)})`,
      whatsapp: {},
    };
  }
}

// ------------------------------------------------------------
// API ROUTES
// ------------------------------------------------------------
app.get('/api/overview', async (_req: Request, res: Response) => {
  const [pabxResult, kanbanResult, whatsResult] = await Promise.all([
    fetchPabx(secretsStore),
    fetchKanban(secretsStore),
    fetchWhatsFlux(secretsStore),
  ]);

  res.json({
    pabx: pabxResult,
    kanban: kanbanResult,
    whatsflux: whatsResult,
    demoMode,
    secretsConfigured: {
      pabx: Boolean(secretsStore.EMAIL && secretsStore.SENHA),
      kanban: Boolean(secretsStore.KANBAN_USER && secretsStore.KANBAN_PASS),
      whatsflux: Boolean(secretsStore.WHATSFLUX_EMAIL && secretsStore.WHATSFLUX_SENHA),
    },
    timestamp: new Date().toISOString(),
  });
});

app.post('/api/secrets', (req: Request, res: Response) => {
  const { EMAIL, SENHA, KANBAN_USER, KANBAN_PASS, WHATSFLUX_EMAIL, WHATSFLUX_SENHA, demo } = req.body;
  if (EMAIL !== undefined) secretsStore.EMAIL = EMAIL;
  if (SENHA !== undefined) secretsStore.SENHA = SENHA;
  if (KANBAN_USER !== undefined) secretsStore.KANBAN_USER = KANBAN_USER;
  if (KANBAN_PASS !== undefined) secretsStore.KANBAN_PASS = KANBAN_PASS;
  if (WHATSFLUX_EMAIL !== undefined) secretsStore.WHATSFLUX_EMAIL = WHATSFLUX_EMAIL;
  if (WHATSFLUX_SENHA !== undefined) secretsStore.WHATSFLUX_SENHA = WHATSFLUX_SENHA;
  if (demo !== undefined) demoMode = Boolean(demo);

  res.json({
    success: true,
    demoMode,
    secretsConfigured: {
      pabx: Boolean(secretsStore.EMAIL && secretsStore.SENHA),
      kanban: Boolean(secretsStore.KANBAN_USER && secretsStore.KANBAN_PASS),
      whatsflux: Boolean(secretsStore.WHATSFLUX_EMAIL && secretsStore.WHATSFLUX_SENHA),
    },
  });
});

app.post('/api/kanban/task', (req: Request, res: Response) => {
  const { action, taskId, titulo } = req.body;
  const tarefas = carregarTarefasSalvas();

  if (action === 'create') {
    const id = taskId || String(Date.now()).slice(-4);
    tarefas[id] = {
      titulo: titulo || `Atendimento emergencial #${id}`,
      data_criacao: 'Agora',
      status: 'Pendente',
    };
    salvarTarefas(tarefas);
    pendingAlert = true;
    return res.json({ success: true, action: 'created', id, tarefas });
  }

  if (action === 'delete') {
    if (tarefas[taskId]) {
      delete tarefas[taskId];
      salvarTarefas(tarefas);
    }
    return res.json({ success: true, action: 'deleted', id: taskId, tarefas });
  }

  return res.status(400).json({ error: 'Ação inválida' });
});

app.get('/api/python-code', (_req: Request, res: Response) => {
  try {
    const code = fs.readFileSync(PYTHON_FILE, 'utf-8');
    res.json({ code });
  } catch (err) {
    res.status(500).json({ error: 'Erro ao ler arquivo Python original.' });
  }
});

// ------------------------------------------------------------
// SERVER SETUP & VITE MOUNT
// ------------------------------------------------------------
async function startServer() {
  if (process.env.NODE_ENV === 'production') {
    app.use(express.static(path.join(__dirname, 'dist')));
    app.get('*', (_req, res) => {
      res.sendFile(path.join(__dirname, 'dist', 'index.html'));
    });
  } else {
    const { createServer } = await import('vite');
    const vite = await createServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  }

  app.listen(PORT, () => {
    console.log(`Servidor SGIH Service Desk rodando na porta ${PORT}`);
  });
}

startServer();
