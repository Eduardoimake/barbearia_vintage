/**
 * Roteador SPA próprio (History API).
 * - Rotas com parâmetros (:slug, :id) e carregamento sob demanda das páginas
 * - Proteção de rotas /painel/* (o backend continua sendo a autoridade)
 * - Foco movido para #main-content e anúncio via aria-live após cada navegação
 */
import { setHtml, announce, focusMain } from './utils/dom.js';
import { getErrorMessage } from './utils/errors.js';
import { isAuthenticated, isChecked, restoreSession } from './state/authState.js';
import { LoadingState } from './components/LoadingState.js';
import { ErrorState, bindRetry } from './components/ErrorState.js';
import { EmptyState } from './components/EmptyState.js';

const NOME_SITE = 'Barbearia Vintage & Co.';

/** Tabela de rotas. `auth` exige admin; `visitante` é só para não autenticados. */
const ROTAS = [
  { padrao: '/', layout: 'public', titulo: 'Início', carregar: () => import('./pages/public/HomePage.js') },
  { padrao: '/servicos', layout: 'public', titulo: 'Serviços', carregar: () => import('./pages/public/ServicesPage.js') },
  { padrao: '/servico/:slug', layout: 'public', titulo: 'Serviço', carregar: () => import('./pages/public/ServiceDetailPage.js') },
  { padrao: '/equipe', layout: 'public', titulo: 'Equipe', carregar: () => import('./pages/public/TeamPage.js') },
  { padrao: '/contato', layout: 'public', titulo: 'Contato', carregar: () => import('./pages/public/ContactPage.js') },
  { padrao: '/painel/login', layout: 'login', visitante: true, titulo: 'Entrar no painel', carregar: () => import('./pages/admin/LoginPage.js') },
  { padrao: '/painel', layout: 'admin', auth: true, titulo: 'Dashboard', carregar: () => import('./pages/admin/DashboardPage.js') },
  { padrao: '/painel/servicos', layout: 'admin', auth: true, titulo: 'Serviços', carregar: () => import('./pages/admin/ServicesAdminPage.js') },
  { padrao: '/painel/servicos/novo', layout: 'admin', auth: true, titulo: 'Novo serviço', carregar: () => import('./pages/admin/ServiceFormPage.js') },
  { padrao: '/painel/servicos/:id/editar', layout: 'admin', auth: true, titulo: 'Editar serviço', carregar: () => import('./pages/admin/ServiceFormPage.js') },
  { padrao: '/painel/categorias', layout: 'admin', auth: true, titulo: 'Categorias', carregar: () => import('./pages/admin/CategoriesAdminPage.js') },
  { padrao: '/painel/barbeiros', layout: 'admin', auth: true, titulo: 'Barbeiros', carregar: () => import('./pages/admin/BarbersAdminPage.js') },
  { padrao: '/painel/promocoes', layout: 'admin', auth: true, titulo: 'Promoções', carregar: () => import('./pages/admin/PromotionsAdminPage.js') },
  { padrao: '/painel/barbearia', layout: 'admin', auth: true, titulo: 'Barbearia', carregar: () => import('./pages/admin/StoreAdminPage.js') },
];

const ROTA_NAO_ENCONTRADA = { layout: 'public', titulo: 'Página não encontrada', carregar: null };

/** Rotas com o padrão já convertido em expressão regular. */
const ROTAS_COMPILADAS = ROTAS.map((rota) => {
  const nomes = [];
  const partes = rota.padrao
    .replace(/\/+$/, '')
    .split('/')
    .map((segmento) => {
      if (segmento.startsWith(':')) {
        nomes.push(segmento.slice(1));
        return '([^/]+)';
      }
      return segmento.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    });
  return { rota, nomes, regex: new RegExp(`^${partes.join('/')}/?$`) };
});

let layouts = {};
let elementoApp = null;
let layoutAtual = null;
let idNavegacao = 0;
let limpezaPagina = null;
let controladorPagina = null;
let tituloDinamico = null;
let ultimoCaminhoBusca = null; // pathname + search da última página renderizada

/**
 * Registra os layouts (public, admin, login).
 * Cada layout expõe mount(app) -> HTMLElement e update(path).
 * @param {Record<string, {mount: Function, update?: Function}>} mapa
 */
export function registerLayouts(mapa) {
  layouts = mapa;
}

/** @returns {string} Caminho atual (sem barra final, exceto a raiz). */
export function getCurrentPath() {
  const caminho = window.location.pathname.replace(/\/+$/, '');
  return caminho || '/';
}

/**
 * Encontra a rota correspondente ao caminho.
 * @param {string} caminho
 * @returns {{rota: object, params: Record<string,string>}|null}
 */
function casar(caminho) {
  for (const item of ROTAS_COMPILADAS) {
    const resultado = item.regex.exec(caminho);
    if (resultado) {
      const params = {};
      item.nomes.forEach((nome, i) => {
        try {
          params[nome] = decodeURIComponent(resultado[i + 1]);
        } catch {
          params[nome] = resultado[i + 1];
        }
      });
      return { rota: item.rota, params };
    }
  }
  return null;
}

/**
 * Rola até o elemento do hash e move o foco para ele.
 * @param {string} hash Ex.: "#promocoes".
 * @returns {boolean} true se o elemento existe.
 */
function irParaHash(hash) {
  if (!hash || hash.length < 2) return false;
  let id = hash.slice(1);
  try {
    id = decodeURIComponent(id);
  } catch {
    /* mantém o id original */
  }
  const elemento = document.getElementById(id);
  if (!elemento) return false;
  elemento.scrollIntoView();
  if (!elemento.hasAttribute('tabindex')) elemento.setAttribute('tabindex', '-1');
  elemento.focus({ preventScroll: true });
  return true;
}

/**
 * Atualiza a query string sem recarregar a página (ex.: filtros).
 * @param {Record<string, string|number|null|undefined>} novos Valores vazios removem o parâmetro.
 */
export function updateQuery(novos) {
  const url = new URL(window.location.href);
  Object.entries(novos).forEach(([chave, valor]) => {
    if (valor === null || valor === undefined || String(valor) === '') url.searchParams.delete(chave);
    else url.searchParams.set(chave, String(valor));
  });
  window.history.replaceState(null, '', `${url.pathname}${url.search}${url.hash}`);
  ultimoCaminhoBusca = `${url.pathname}${url.search}`;
}

/**
 * Navega para um destino interno.
 * @param {string} destino Ex.: "/servicos?category=barba".
 * @param {{replace?: boolean}} [opcoes]
 * @returns {Promise<void>}
 */
export function navigate(destino, opcoes = {}) {
  const url = new URL(destino, window.location.origin);
  if (url.origin !== window.location.origin) {
    window.location.assign(destino);
    return Promise.resolve();
  }
  const novo = `${url.pathname}${url.search}${url.hash}`;
  const mesmaPagina = `${url.pathname}${url.search}` === ultimoCaminhoBusca;

  if (opcoes.replace) window.history.replaceState(null, '', novo);
  else window.history.pushState(null, '', novo);

  // Mudou apenas o hash: não renderiza de novo, só rola até a seção
  if (mesmaPagina && url.hash) {
    irParaHash(url.hash);
    return Promise.resolve();
  }
  return resolver();
}

/**
 * Exibe um estado de erro no container principal.
 * @param {HTMLElement} principal
 * @param {unknown} erro
 */
function mostrarErro(principal, erro) {
  setHtml(
    principal,
    ErrorState({ titulo: 'Não foi possível abrir esta página', mensagem: getErrorMessage(erro) }),
  );
  bindRetry(principal, () => resolver());
}

/** Resolve a URL atual, aplica guardas, monta o layout e renderiza a página. */
async function resolver() {
  idNavegacao += 1;
  const id = idNavegacao;

  if (typeof limpezaPagina === 'function') {
    try {
      limpezaPagina();
    } catch {
      /* limpeza não deve quebrar a navegação */
    }
  }
  limpezaPagina = null;
  if (controladorPagina) controladorPagina.abort();
  controladorPagina = new AbortController();
  tituloDinamico = null;

  const url = new URL(window.location.href);
  const caminho = getCurrentPath();
  const encontrada = casar(caminho);
  const rota = encontrada ? encontrada.rota : ROTA_NAO_ENCONTRADA;
  const params = encontrada ? encontrada.params : {};

  // Guardas de rota (melhoram a experiência; o backend decide de fato)
  if (rota.auth || rota.visitante) {
    if (!isChecked()) {
      await restoreSession();
      if (id !== idNavegacao) return;
    }
    if (rota.auth && !isAuthenticated()) {
      const proximo = encodeURIComponent(`${caminho}${url.search}`);
      await navigate(`/painel/login?next=${proximo}`, { replace: true });
      return;
    }
    if (rota.visitante && isAuthenticated()) {
      await navigate('/painel', { replace: true });
      return;
    }
  }

  // Monta o layout somente quando ele muda
  const layout = layouts[rota.layout];
  if (layoutAtual !== rota.layout) {
    layout.mount(elementoApp);
    layoutAtual = rota.layout;
  }
  if (typeof layout.update === 'function') layout.update(caminho);

  const principal = document.getElementById('main-content');
  ultimoCaminhoBusca = `${url.pathname}${url.search}`;
  setHtml(principal, LoadingState('Carregando página...'));

  const ctx = {
    params,
    query: Object.fromEntries(url.searchParams.entries()),
    path: caminho,
    root: principal,
    signal: controladorPagina.signal,
    navigate,
    setTitle: (titulo) => {
      tituloDinamico = titulo;
    },
  };

  try {
    if (rota.carregar) {
      const modulo = await rota.carregar();
      if (id !== idNavegacao) return;
      principal.replaceChildren();
      const limpeza = await modulo.render(ctx);
      if (id !== idNavegacao) {
        if (typeof limpeza === 'function') limpeza();
        return;
      }
      limpezaPagina = typeof limpeza === 'function' ? limpeza : null;
    } else {
      setHtml(
        principal,
        EmptyState({
          titulo: 'Página não encontrada',
          mensagem: 'O endereço acessado não existe ou foi movido.',
          acao: { href: '/', rotulo: 'Voltar ao início' },
        }),
      );
    }
  } catch (erro) {
    if (erro?.name === 'AbortError' || id !== idNavegacao) return;
    mostrarErro(principal, erro);
  }

  if (id !== idNavegacao) return;
  const tituloPagina = tituloDinamico || rota.titulo;
  document.title = `${tituloPagina} | ${NOME_SITE}`;
  announce(`Página carregada: ${tituloPagina}`);

  // Foco: seção do hash, se existir; senão, #main-content
  if (!irParaHash(url.hash)) {
    window.scrollTo(0, 0);
    focusMain();
  }
}

/**
 * Trata cliques em links internos, sem recarregar a página.
 * @param {MouseEvent} evento
 */
function aoClicarLink(evento) {
  if (evento.defaultPrevented || evento.button !== 0) return;
  if (evento.metaKey || evento.ctrlKey || evento.shiftKey || evento.altKey) return;
  const ancora = evento.target.closest ? evento.target.closest('a') : null;
  if (!ancora) return;
  if (ancora.target && ancora.target !== '_self') return;
  if (ancora.hasAttribute('download')) return;

  const href = ancora.getAttribute('href');
  if (!href || href.startsWith('#')) return; // âncoras puras seguem o comportamento do navegador/skip link

  const url = new URL(ancora.href, window.location.origin);
  if (url.origin !== window.location.origin) return;
  // Caminhos do backend (mídia, API, admin do Django) não pertencem à SPA
  if (/^\/(media|api|admin|static)\//.test(url.pathname)) return;

  evento.preventDefault();
  navigate(`${url.pathname}${url.search}${url.hash}`);
}

/** Trata os botões voltar/avançar do navegador. */
function aoMudarHistorico() {
  const url = new URL(window.location.href);
  if (`${url.pathname}${url.search}` === ultimoCaminhoBusca) {
    if (url.hash) irParaHash(url.hash);
    return;
  }
  resolver();
}

/**
 * Inicia o roteador.
 * @param {HTMLElement} app Elemento raiz da aplicação.
 */
export function startRouter(app) {
  elementoApp = app;
  document.addEventListener('click', aoClicarLink);
  window.addEventListener('popstate', aoMudarHistorico);
  resolver();
}