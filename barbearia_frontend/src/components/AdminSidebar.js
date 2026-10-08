/**
 * Barra lateral do painel administrativo.
 */
import { html, raw } from '../utils/dom.js';

const ITENS = [
  { href: '/painel', rotulo: 'Dashboard', exato: true },
  { href: '/painel/servicos', rotulo: 'Serviços' },
  { href: '/painel/categorias', rotulo: 'Categorias' },
  { href: '/painel/barbeiros', rotulo: 'Barbeiros' },
  { href: '/painel/promocoes', rotulo: 'Promoções' },
  { href: '/painel/barbearia', rotulo: 'Barbearia' },
];

/**
 * @param {{path?: string, user?: object|null}} opcoes
 * @returns {object} HTML seguro.
 */
export function AdminSidebar({ path = '/painel', user = null } = {}) {
  const ativo = (item) => (item.exato ? path === item.href : path === item.href || path.startsWith(`${item.href}/`));

  return html`<aside class="admin-sidebar">
    <div class="admin-sidebar__top">
      <a class="admin-brand" href="/painel">
        <span class="brand__top">BARBEARIA</span>
        <span class="brand__bottom">Vintage Co. · Painel</span>
      </a>
      <button type="button" class="nav-toggle" data-action="toggle-sidebar" aria-expanded="false" aria-controls="admin-nav">Menu</button>
    </div>

    <nav id="admin-nav" class="admin-nav" aria-label="Menu administrativo">
      <ul class="admin-nav__list">
        ${ITENS.map(
          (item) => html`<li><a class="admin-nav__link" href="${item.href}" ${ativo(item) ? raw('aria-current="page"') : ''}>${item.rotulo}</a></li>`,
        )}
      </ul>

      <div class="admin-sidebar__footer">
        ${user?.username ? html`<p class="admin-user">Conectado como <strong>${user.username}</strong></p>` : ''}
        <a class="btn btn--ghost btn--sm" href="/">Ver site</a>
        <button type="button" class="btn btn--ghost btn--sm" data-action="logout">Sair</button>
      </div>
    </nav>
  </aside>`;
}

/**
 * Liga o menu móvel da sidebar (aria-expanded) e o fechamento com Esc.
 * @param {HTMLElement} raizSidebar
 */
export function bindAdminSidebar(raizSidebar) {
  const botao = raizSidebar.querySelector('[data-action="toggle-sidebar"]');
  const nav = raizSidebar.querySelector('#admin-nav');
  if (!botao || !nav) return;

  const definir = (aberto) => {
    botao.setAttribute('aria-expanded', String(aberto));
    nav.classList.toggle('is-open', aberto);
  };

  botao.addEventListener('click', () => definir(botao.getAttribute('aria-expanded') !== 'true'));
  nav.addEventListener('click', (evento) => {
    if (evento.target instanceof Element && evento.target.closest('a')) definir(false);
  });
  raizSidebar.addEventListener('keydown', (evento) => {
    if (evento.key === 'Escape' && botao.getAttribute('aria-expanded') === 'true') {
      definir(false);
      botao.focus();
    }
  });
}