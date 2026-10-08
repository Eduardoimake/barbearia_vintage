/**
 * Estado de carregamento acessível.
 */
import { html } from '../utils/dom.js';

/**
 * @param {string} [mensagem] Texto anunciado a leitores de tela.
 * @returns {object} HTML seguro.
 */
export function LoadingState(mensagem = 'Carregando...') {
  return html`<div class="state state--loading" role="status" aria-live="polite">
    <span class="spinner" aria-hidden="true"></span>
    <p class="state__text">${mensagem}</p>
  </div>`;
}