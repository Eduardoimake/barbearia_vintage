/**
 * Paginação acessível. Os botões usam data-page.
 */
import { html, raw } from '../utils/dom.js';

/**
 * @param {{page?: number, count?: number, pageSize?: number, rotulo?: string}} opcoes
 * @returns {object} HTML seguro (vazio quando há uma única página).
 */
export function Pagination({ page = 1, count = 0, pageSize = 12, rotulo = 'Paginação' } = {}) {
  const total = Math.max(1, Math.ceil(count / pageSize));
  if (total <= 1) return html``;

  const inicio = Math.max(1, page - 2);
  const fim = Math.min(total, page + 2);
  const paginas = [];
  for (let p = inicio; p <= fim; p += 1) paginas.push(p);

  return html`<nav class="pagination" aria-label="${rotulo}">
    <button type="button" class="pagination__btn" data-page="${page - 1}" ${page <= 1 ? raw('disabled') : ''}>Anterior</button>
    <ul class="pagination__list">
      ${paginas.map(
        (p) => html`<li>
          <button type="button" class="pagination__btn ${p === page ? 'is-current' : ''}" data-page="${p}" aria-label="Página ${p}" ${p === page ? raw('aria-current="page"') : ''}>${p}</button>
        </li>`,
      )}
    </ul>
    <button type="button" class="pagination__btn" data-page="${page + 1}" ${page >= total ? raw('disabled') : ''}>Próxima</button>
    <p class="pagination__info">Página ${page} de ${total} · ${count} ${count === 1 ? 'item' : 'itens'}</p>
  </nav>`;
}

/**
 * Liga os cliques de paginação em um container (chame UMA vez por container).
 * @param {HTMLElement} container Elemento que permanece no DOM entre renderizações.
 * @param {(pagina: number) => void} aoMudar
 */
export function bindPagination(container, aoMudar) {
  container.addEventListener('click', (evento) => {
    const botao = evento.target instanceof Element ? evento.target.closest('button[data-page]') : null;
    if (!botao || botao.disabled) return;
    const pagina = Number.parseInt(botao.dataset.page, 10);
    if (Number.isFinite(pagina) && pagina >= 1) aoMudar(pagina);
  });
}