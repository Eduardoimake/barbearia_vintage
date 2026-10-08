/**
 * Estado de erro com botão "Tentar novamente" (role="alert").
 */
import { html, setHtml } from '../utils/dom.js';
import { getErrorMessage } from '../utils/errors.js';

/**
 * @param {{titulo?: string, mensagem?: string, tentarNovamente?: boolean}} [opcoes]
 * @returns {object} HTML seguro.
 */
export function ErrorState({
  titulo = 'Não foi possível carregar',
  mensagem = 'Tente novamente em instantes.',
  tentarNovamente = true,
} = {}) {
  return html`<div class="state state--error" role="alert">
    <h3 class="state__title">${titulo}</h3>
    <p class="state__text">${mensagem}</p>
    ${tentarNovamente
      ? html`<button type="button" class="btn btn--outline btn--sm" data-action="retry">Tentar novamente</button>`
      : ''}
  </div>`;
}

/**
 * Liga o botão "Tentar novamente" dentro do container.
 * @param {ParentNode} container
 * @param {() => void} acao
 */
export function bindRetry(container, acao) {
  const botao = container.querySelector('[data-action="retry"]');
  if (botao) botao.addEventListener('click', acao, { once: true });
}

/**
 * Atalho: desenha o erro no container e liga o retry.
 * @param {HTMLElement} container
 * @param {unknown} erro
 * @param {() => void} [aoTentar]
 * @param {string} [titulo]
 */
export function renderError(container, erro, aoTentar, titulo) {
  setHtml(
    container,
    ErrorState({
      titulo: titulo || 'Não foi possível carregar',
      mensagem: getErrorMessage(erro),
      tentarNovamente: typeof aoTentar === 'function',
    }),
  );
  if (aoTentar) bindRetry(container, aoTentar);
}