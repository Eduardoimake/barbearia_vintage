/**
 * Tabela administrativa reutilizável e acessível.
 * Todo valor é escapado; colunas com `render` devem retornar HTML produzido por `html`.
 */
import { html } from '../utils/dom.js';

/**
 * @param {{
 *   legenda: string,
 *   colunas: Array<{chave?: string, rotulo: string, render?: (linha: object) => any}>,
 *   linhas: object[],
 *   acoes?: (linha: object) => any,
 *   vazio?: string
 * }} opcoes
 * @returns {object} HTML seguro.
 */
export function AdminTable({ legenda, colunas, linhas, acoes = null, vazio = 'Nenhum registro encontrado.' }) {
  if (!linhas.length) {
    return html`<p class="admin-empty" role="status">${vazio}</p>`;
  }

  return html`<div class="table-wrap" role="region" aria-label="${legenda}" tabindex="0">
    <table class="admin-table">
      <caption class="sr-only">${legenda}</caption>
      <thead>
        <tr>
          ${colunas.map((c) => html`<th scope="col">${c.rotulo}</th>`)}
          ${acoes ? html`<th scope="col">Ações</th>` : ''}
        </tr>
      </thead>
      <tbody>
        ${linhas.map(
          (linha) => html`<tr>
            ${colunas.map(
              (c) => html`<td data-label="${c.rotulo}">${c.render ? c.render(linha) : linha[c.chave]}</td>`,
            )}
            ${acoes ? html`<td data-label="Ações" class="admin-table__actions">${acoes(linha)}</td>` : ''}
          </tr>`,
        )}
      </tbody>
    </table>
  </div>`;
}