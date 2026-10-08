/**
 * Card de categoria. Leva à lista de serviços filtrada pelo slug.
 * Campos usados: nome, slug, descricao_curta.
 */
import { html } from '../utils/dom.js';

/**
 * @param {object} categoria Categoria pública.
 * @returns {object} HTML seguro.
 */
export function CategoryCard(categoria) {
  const href = `/servicos?category=${encodeURIComponent(categoria.slug)}`;
  return html`<a class="category-card" href="${href}">
    <h3 class="category-card__title">${categoria.nome}</h3>
    ${categoria.descricao_curta ? html`<p class="category-card__text">${categoria.descricao_curta}</p>` : ''}
    <span class="category-card__link">Ver serviços <span aria-hidden="true">→</span></span>
  </a>`;
}