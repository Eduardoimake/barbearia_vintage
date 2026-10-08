/**
 * Ponto de entrada da SPA: estilos, layouts, eventos globais e roteador.
 */
import './styles/variables.css';
import './styles/reset.css';
import './styles/global.css';
import './styles/components.css';
import './styles/public.css';
import './styles/home.css';
import './styles/admin.css';

import { startRouter, registerLayouts, navigate, getCurrentPath } from './router.js';
import { setAuthFailureHandler } from './api/client.js';
import { clearSession, getUser, signOut } from './state/authState.js';
import { getStoreConfig } from './state/appState.js';
import { html, setHtml, focusMain } from './utils/dom.js';
import { getErrorMessage } from './utils/errors.js';
import { SiteHeader, bindSiteHeader } from './components/SiteHeader.js';
import { SiteFooter } from './components/SiteFooter.js';
import { AdminSidebar, bindAdminSidebar } from './components/AdminSidebar.js';
import { showToast } from './components/Toast.js';

const app = document.getElementById('app');

/* ---------- Layout público: header + main + footer ---------- */
const layoutPublico = {
  caminho: '/',
  loja: null,

  /**
   * Monta a estrutura pública e carrega os dados da loja em segundo plano.
   * @param {HTMLElement} raiz
   */
  mount(raiz) {
    setHtml(
      raiz,
      html`<div class="site-shell">
        <div data-slot="header"></div>
        <main id="main-content" class="site-main" tabindex="-1"></main>
        <div data-slot="footer"></div>
      </div>`,
    );
    this.loja = null;
    this.pintar();
    getStoreConfig()
      .then((loja) => {
        this.loja = loja;
        this.pintar();
      })
      .catch(() => {
        // Sem dados da loja, o header e o rodapé usam textos padrão
      });
  },

  /** Redesenha header e footer com o estado atual. */
  pintar() {
    const cabecalho = document.querySelector('[data-slot="header"]');
    const rodape = document.querySelector('[data-slot="footer"]');
    if (!cabecalho || !rodape) return;
    setHtml(cabecalho, SiteHeader({ loja: this.loja, path: this.caminho }));
    setHtml(rodape, SiteFooter({ loja: this.loja }));
    bindSiteHeader(cabecalho);
  },

  /**
   * Atualiza o item ativo do menu.
   * @param {string} caminho
   */
  update(caminho) {
    this.caminho = caminho;
    this.pintar();
  },
};

/* ---------- Layout administrativo: sidebar + main ---------- */
const layoutAdmin = {
  caminho: '/painel',

  /** @param {HTMLElement} raiz */
  mount(raiz) {
    setHtml(
      raiz,
      html`<div class="admin-shell">
        <div data-slot="sidebar"></div>
        <main id="main-content" class="admin-main" tabindex="-1"></main>
      </div>`,
    );
    this.pintar();
  },

  /** Redesenha a sidebar. */
  pintar() {
    const lateral = document.querySelector('[data-slot="sidebar"]');
    if (!lateral) return;
    setHtml(lateral, AdminSidebar({ path: this.caminho, user: getUser() }));
    bindAdminSidebar(lateral);
  },

  /** @param {string} caminho */
  update(caminho) {
    this.caminho = caminho;
    this.pintar();
  },
};

/* ---------- Layout de login: apenas o main ---------- */
const layoutLogin = {
  /** @param {HTMLElement} raiz */
  mount(raiz) {
    setHtml(raiz, html`<main id="main-content" class="login-main" tabindex="-1"></main>`);
  },
};

registerLayouts({ public: layoutPublico, admin: layoutAdmin, login: layoutLogin });

/* ---------- Falha de autenticação em rota administrativa (401/403) ---------- */
setAuthFailureHandler(() => {
  clearSession();
  const caminho = getCurrentPath();
  if (caminho.startsWith('/painel') && caminho !== '/painel/login') {
    showToast('Sua sessão expirou ou não é válida. Entre novamente.', 'error');
    navigate(`/painel/login?next=${encodeURIComponent(caminho)}`, { replace: true });
  }
});

/* ---------- Eventos globais (delegação) ---------- */
document.addEventListener('click', async (evento) => {
  const alvo = evento.target instanceof Element ? evento.target : null;
  if (!alvo) return;

  // Skip link: move o foco para o conteúdo principal
  if (alvo.closest('[data-skip-link]')) {
    evento.preventDefault();
    focusMain();
    return;
  }

  // Voltar ao topo
  if (alvo.closest('[data-action="scroll-top"]')) {
    window.scrollTo({ top: 0 });
    focusMain();
    return;
  }

  // Sair do painel
  const botaoSair = alvo.closest('[data-action="logout"]');
  if (botaoSair) {
    botaoSair.setAttribute('disabled', 'true');
    try {
      await signOut();
      showToast('Sessão encerrada com sucesso.', 'success');
    } catch (erro) {
      showToast(getErrorMessage(erro), 'error');
    }
    navigate('/painel/login', { replace: true });
  }
});

startRouter(app);