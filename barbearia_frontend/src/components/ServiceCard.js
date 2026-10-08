/**
 * Card de serviço: imagem, categoria, nome, descrição, preço, duração e ações.
 * Campos usados: nome, slug, descricao_curta, preco, duracao_minutos,
 * imagem_principal, alt_text, categoria.nome.
 */
import { html } from '../utils/dom.js';
import { resolveImageUrl } from '../utils/imageUrl.js';
import { formatPrice, formatDuration } from '../utils/formatters.js';
import { whatsappButton, buildServiceMessage } from '../utils/whatsapp.js';

/**
 * @param {object} servico Serviço da listagem pública.
 * @param {object|null} [loja] Dados públicos da barbearia (para o WhatsApp).
 * @returns {object} HTML seguro.
 */
export function ServiceCard(servico, loja = null) {
  const imagem = resolveImageUrl(servico.imagem_principal);
  const href = `/servico/${encodeURIComponent(servico.slug)}`;

  return html`<article class="service-card">
    <div class="service-card__media">
      ${imagem
        ? html`<img src="${imagem}" alt="${servico.alt_text || servico.nome}" loading="lazy" />`
        : html`<span class="media-placeholder" aria-hidden="true">V Co.</span>`}
    </div>
    <div class="service-card__body">
      ${servico.categoria?.nome ? html`<p class="service-card__category">${servico.categoria.nome}</p>` : ''}
      <h3 class="service-card__title"><a href="${href}">${servico.nome}</a></h3>
      <p class="service-card__text">${servico.descricao_curta}</p>
      <dl class="service-card__meta">
        <div><dt class="sr-only">Preço</dt><dd class="service-card__price">${formatPrice(servico.preco)}</dd></div>
        <div><dt class="sr-only">Duração</dt><dd class="service-card__duration">${formatDuration(servico.duracao_minutos)}</dd></div>
      </dl>
      <div class="service-card__actions">
        <a class="btn btn--outline btn--sm" href="${href}">Ver detalhes</a>
        ${whatsappButton({
          numero: loja?.numero_whatsapp,
          mensagem: buildServiceMessage(servico.nome, loja?.nome_da_barbearia),
          rotulo: 'Agendar',
          classe: 'btn btn--primary btn--sm',
        })}
      </div>
    </div>
  </article>`;
}