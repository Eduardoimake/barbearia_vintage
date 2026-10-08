/**
 * Equipe (/equipe): barbeiros ativos.
 */
import { html, setHtml } from '../../utils/dom.js';
import * as publicApi from '../../api/publicApi.js';
import { LoadingState } from '../../components/LoadingState.js';
import { EmptyState } from '../../components/EmptyState.js';
import { renderError } from '../../components/ErrorState.js';
import { BarberCard } from '../../components/BarberCard.js';

/**
 * Renderiza a lista de barbeiros.
 * @param {object} ctx Contexto do roteador.
 * @returns {Promise<Function>} Função de limpeza.
 */
export async function render(ctx) {
  const { root, signal } = ctx;

  setHtml(
    root,
    html`<div class="container page">
      <header class="page-header">
        <h1 class="page-title">Nossa equipe</h1>
        <p class="page-subtitle">Profissionais dedicados à técnica clássica e ao acabamento contemporâneo.</p>
      </header>
      <div data-lista></div>
    </div>`,
  );
  const lista = root.querySelector('[data-lista]');

  const carregar = async () => {
    setHtml(lista, LoadingState('Carregando equipe...'));
    try {
      const barbeiros = await publicApi.getBarbers(signal);
      if (signal.aborted) return;
      if (!barbeiros.length) {
        setHtml(lista, EmptyState({ titulo: 'Equipe em atualização', mensagem: 'Os barbeiros aparecerão aqui assim que forem cadastrados.' }));
        return;
      }
      setHtml(lista, html`<div class="grid grid--team">${barbeiros.map((b) => BarberCard(b))}</div>`);
    } catch (erro) {
      if (signal.aborted || erro?.name === 'AbortError') return;
      renderError(lista, erro, carregar, 'Não foi possível carregar a equipe');
    }
  };

  await carregar();
  return () => {};
}