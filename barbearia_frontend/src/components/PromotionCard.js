/**
 * Card de promoção.
 * Campos usados: titulo, descricao, imagem, servico_vinculado (objeto), data_fim.
 */
import { html } from '../utils/dom.js';
import { resolveImageUrl } from '../utils/imageUrl.js';
import { formatDate } from '../utils/formatters.js';

/**
 * @param {object} promocao Promoção pública.
 * @returns {object} HTML seguro.
 */
export function PromotionCard(promocao) {
  const imagem = resolveImageUrl(promocao.imagem);
  const servico = promocao.servico_vinculado;

  return html`<article class="promo-card">
    ${imagem
      ? html`<div class="promo-card__media"><img src="${imagem}" alt="${promocao.titulo}" loading="lazy" /></div>`
      : ''}
    <div class="promo-card__body">
      <h3 class="promo-card__title">${promocao.titulo}</h3>
      <p class="promo-card__text">${promocao.descricao}</p>
      ${promocao.data_fim ? html`<p class="promo-card__validity">Válida até ${formatDate(promocao.data_fim)}</p>` : ''}
      ${servico?.slug
        ? html`<a class="btn btn--outline btn--sm" href="/servico/${encodeURIComponent(servico.slug)}">Ver serviço: ${servico.nome}</a>`
        : ''}
    </div>
  </article>`;
}