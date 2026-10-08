/**
 * Card de barbeiro.
 * Campos usados: nome, especialidade, descricao_curta, foto_principal, alt_text.
 */
import { html } from '../utils/dom.js';
import { resolveImageUrl } from '../utils/imageUrl.js';

/**
 * @param {object} barbeiro Barbeiro público.
 * @returns {object} HTML seguro.
 */
export function BarberCard(barbeiro) {
  const foto = resolveImageUrl(barbeiro.foto_principal);
  return html`<article class="barber-card">
    <div class="barber-card__media">
      ${foto
        ? html`<img src="${foto}" alt="${barbeiro.alt_text || `Foto de ${barbeiro.nome}`}" loading="lazy" />`
        : html`<span class="media-placeholder" aria-hidden="true">V Co.</span>`}
    </div>
    <div class="barber-card__body">
      <h3 class="barber-card__name">${barbeiro.nome}</h3>
      <p class="barber-card__role">${barbeiro.especialidade}</p>
      <p class="barber-card__text">${barbeiro.descricao_curta}</p>
    </div>
  </article>`;
}