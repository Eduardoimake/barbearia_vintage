/**
 * Rodapé do site público (estrutura de homePage.html):
 * marca, navegação, informações, mensagem, direitos e "Voltar ao topo".
 */
import { html } from '../utils/dom.js';
import { whatsappButton, buildGeneralMessage } from '../utils/whatsapp.js';

/**
 * @param {{loja?: object|null}} opcoes
 * @returns {object} HTML seguro.
 */
export function SiteFooter({ loja = null } = {}) {
  const nome = loja?.nome_da_barbearia || 'Barbearia Vintage & Co.';
  const ano = new Date().getFullYear();

  return html`<footer class="site-footer">
    <div class="container site-footer__grid">
      <div class="site-footer__col">
        <a class="brand brand--footer" href="/" aria-label="${nome} — página inicial">
          <span class="brand__top">BARBEARIA</span>
          <span class="brand__bottom">Vintage Co.</span>
        </a>
        ${loja?.slogan ? html`<p class="site-footer__text">${loja.slogan}</p>` : ''}
      </div>

      <nav class="site-footer__col" aria-label="Navegação do rodapé">
        <h2 class="site-footer__title">Navegação</h2>
        <ul class="site-footer__list">
          <li><a href="/">Início</a></li>
          <li><a href="/servicos">Serviços</a></li>
          <li><a href="/#sobre">Sobre nós</a></li>
          <li><a href="/#como-funciona">Como funciona</a></li>
          <li><a href="/contato">Contato</a></li>
          <li><a href="/painel/login">Área administrativa</a></li>
        </ul>
      </nav>

      <div class="site-footer__col">
        <h2 class="site-footer__title">Informações</h2>
        <ul class="site-footer__list">
          ${loja?.endereco_demo ? html`<li>${loja.endereco_demo}</li>` : ''}
          ${loja?.horario_atendimento ? html`<li>${loja.horario_atendimento}</li>` : ''}
        </ul>
        <div class="site-footer__cta">
          ${whatsappButton({
            numero: loja?.numero_whatsapp,
            mensagem: buildGeneralMessage(nome),
            rotulo: 'Enviar mensagem',
            classe: 'btn btn--outline btn--sm',
          })}
        </div>
      </div>
    </div>

    <div class="site-footer__bottom container">
      <p>© ${ano} ${nome}. Todos os direitos reservados.</p>
      <button type="button" class="btn btn--ghost btn--sm" data-action="scroll-top">Voltar ao topo</button>
    </div>
  </footer>`;
}