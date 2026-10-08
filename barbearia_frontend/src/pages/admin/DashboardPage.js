/**
 * Dashboard (/painel). Mostra apenas as contagens reais de GET /admin/dashboard/:
 * services_count, categories_count, barbers_count, active_promotions_count.
 */
import { html, setHtml } from '../../utils/dom.js';
import { getDashboard } from '../../api/adminApi.js';
import { LoadingState } from '../../components/LoadingState.js';
import { renderError } from '../../components/ErrorState.js';

/**
 * Renderiza o dashboard.
 * @param {object} ctx Contexto do roteador.
 * @returns {Promise<Function>} Função de limpeza.
 */
export async function render(ctx) {
  const { root, signal } = ctx;

  setHtml(
    root,
    html`<div class="admin-page">
      <header class="admin-page__header">
        <h1 class="admin-title">Dashboard</h1>
      </header>
      <div data-conteudo></div>
    </div>`,
  );
  const conteudo = root.querySelector('[data-conteudo]');

  const carregar = async () => {
    setHtml(conteudo, LoadingState('Carregando contagens...'));
    try {
      const dados = await getDashboard(signal);
      if (signal.aborted) return;

      const cartoes = [
        { rotulo: 'Serviços', valor: dados.services_count, href: '/painel/servicos' },
        { rotulo: 'Categorias', valor: dados.categories_count, href: '/painel/categorias' },
        { rotulo: 'Barbeiros', valor: dados.barbers_count, href: '/painel/barbeiros' },
        { rotulo: 'Promoções ativas', valor: dados.active_promotions_count, href: '/painel/promocoes' },
      ];

      setHtml(
        conteudo,
        html`<ul class="stat-grid">
            ${cartoes.map(
              (c) => html`<li>
                <a class="stat-card" href="${c.href}">
                  <span class="stat-card__value">${c.valor ?? 0}</span>
                  <span class="stat-card__label">${c.rotulo}</span>
                </a>
              </li>`,
            )}
          </ul>
          <p class="admin-note">Contagens reais do catálogo. A API não oferece métricas de vendas, faturamento, acessos ou agendamentos.</p>
          <div class="admin-quick">
            <a class="btn btn--primary" href="/painel/servicos/novo">Novo serviço</a>
            <a class="btn btn--ghost" href="/painel/barbearia">Configurar barbearia</a>
            <a class="btn btn--ghost" href="/">Ver site público</a>
          </div>`,
      );
    } catch (erro) {
      if (signal.aborted || erro?.name === 'AbortError') return;
      renderError(conteudo, erro, carregar, 'Não foi possível carregar o dashboard');
    }
  };

  await carregar();
  return () => {};
}