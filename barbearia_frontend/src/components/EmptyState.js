/**
 * Estado vazio (nenhum registro encontrado).
 */
import { html } from '../utils/dom.js';

/**
 * @param {{titulo?: string, mensagem?: string, acao?: {href: string, rotulo: string}}} [opcoes]
 * @returns {object} HTML seguro.
 */
export function EmptyState({
  titulo = 'Nada por aqui ainda',
  mensagem = 'Nenhum item encontrado.',
  acao = null,
} = {}) {
  return html`<div class="state state--empty">
    <h3 class="state__title">${titulo}</h3>
    <p class="state__text">${mensagem}</p>
    ${acao ? html`<a class="btn btn--outline btn--sm" href="${acao.href}">${acao.rotulo}</a>` : ''}
  </div>`;
}