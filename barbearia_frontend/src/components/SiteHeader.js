/**
 * Cabeçalho do site público (estrutura de homePage.html):
 * marca, navegação principal e botão de WhatsApp.
 */
import { html, raw } from '../utils/dom.js';
import { whatsappButton, buildGeneralMessage } from '../utils/whatsapp.js';

/**
 * @param {{loja?: object|null, path?: string}} opcoes
 * @returns {object} HTML seguro.
 */
export function SiteHeader({ loja = null, path = '/' } = {}) {
  const links = [
    { href: '/', rotulo: 'Início', ativo: path === '/' },
    { href: '/servicos', rotulo: 'Serviços', ativo: path === '/servicos' || path.startsWith('/servico/') },
    { href: '/#promocoes', rotulo: 'Promoções', ativo: false },
    { href: '/equipe', rotulo: 'Barbeiros', ativo: path === '/equipe' },
    { href: '/#sobre', rotulo: 'Sobre nós', ativo: false },
    { href: '/contato', rotulo: 'Contato', ativo: path === '/contato' },
  ];
  const nome = loja?.nome_da_barbearia || 'Barbearia Vintage & Co.';

  return html`<header class="site-header">
    <div class="site-header__inner container">
      <a class="brand" href="/" aria-label="${nome} — página inicial">
        <span class="brand__top">BARBEARIA</span>
        <span class="brand__bottom">Vintage Co.</span>
      </a>

      <button type="button" class="nav-toggle" data-action="toggle-menu" aria-expanded="false" aria-controls="site-nav">Menu</button>

      <nav id="site-nav" class="site-nav" aria-label="Navegação principal">
        <ul class="site-nav__list">
          ${links.map(
            (l) => html`<li><a class="site-nav__link" href="${l.href}" ${l.ativo ? raw('aria-current="page"') : ''}>${l.rotulo}</a></li>`,
          )}
        </ul>
        <div class="site-nav__cta">
          ${whatsappButton({
            numero: loja?.numero_whatsapp,
            mensagem: buildGeneralMessage(nome),
            rotulo: 'Falar pelo WhatsApp',
            classe: 'btn btn--primary btn--sm',
          })}
        </div>
      </nav>
    </div>
  </header>`;
}

/**
 * Liga o menu móvel (aria-expanded) e o fechamento com Esc.
 * @param {HTMLElement} raiz Elemento que contém o cabeçalho.
 */
export function bindSiteHeader(raiz) {
  const botao = raiz.querySelector('[data-action="toggle-menu"]');
  const nav = raiz.querySelector('#site-nav');
  if (!botao || !nav) return;

  const definir = (aberto) => {
    botao.setAttribute('aria-expanded', String(aberto));
    nav.classList.toggle('is-open', aberto);
  };

  botao.addEventListener('click', () => {
    definir(botao.getAttribute('aria-expanded') !== 'true');
  });

  nav.addEventListener('click', (evento) => {
    if (evento.target instanceof Element && evento.target.closest('a')) definir(false);
  });

  raiz.addEventListener('keydown', (evento) => {
    if (evento.key === 'Escape' && botao.getAttribute('aria-expanded') === 'true') {
      definir(false);
      botao.focus();
    }
  });
}