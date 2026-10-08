/**
 * Detalhe do serviço (/servico/:slug).
 * Campos usados: nome, categoria, descricao_curta, descricao_completa,
 * preco, duracao_minutos, imagem_principal, alt_text.
 */
import { html, setHtml } from '../../utils/dom.js';
import * as publicApi from '../../api/publicApi.js';
import { getStoreConfig } from '../../state/appState.js';
import { LoadingState } from '../../components/LoadingState.js';
import { EmptyState } from '../../components/EmptyState.js';
import { renderError } from '../../components/ErrorState.js';
import { resolveImageUrl } from '../../utils/imageUrl.js';
import { formatPrice, formatDuration } from '../../utils/formatters.js';
import { whatsappButton, buildServiceMessage } from '../../utils/whatsapp.js';

/**
 * Renderiza o detalhe de um serviço publicado.
 * @param {object} ctx Contexto do roteador.
 * @returns {Promise<Function>} Função de limpeza.
 */
export async function render(ctx) {
  const { root, params, signal } = ctx;

  const carregar = async () => {
    setHtml(root, html`<div class="container page">${LoadingState('Carregando serviço...')}</div>`);

    try {
      const [servico, loja] = await Promise.all([
        publicApi.getService(params.slug, signal),
        getStoreConfig().catch(() => null),
      ]);
      if (signal.aborted) return;

      ctx.setTitle(servico.nome);
      const imagem = resolveImageUrl(servico.imagem_principal);
      const paragrafos = String(servico.descricao_completa || '')
        .split(/\n{2,}/)
        .map((p) => p.trim())
        .filter(Boolean);

      setHtml(
        root,
        html`<div class="container page">
          <nav aria-label="Trilha de navegação">
            <ol class="breadcrumb">
              <li><a href="/">Início</a></li>
              <li><a href="/servicos">Serviços</a></li>
              <li aria-current="page">${servico.nome}</li>
            </ol>
          </nav>

          <article class="service-detail">
            <div class="service-detail__media">
              ${imagem
                ? html`<img src="${imagem}" alt="${servico.alt_text || servico.nome}" />`
                : html`<span class="media-placeholder" aria-hidden="true">V Co.</span>`}
            </div>
            <div class="service-detail__content">
              ${servico.categoria?.nome ? html`<p class="eyebrow">${servico.categoria.nome}</p>` : ''}
              <h1 class="page-title">${servico.nome}</h1>
              <p class="service-detail__lead">${servico.descricao_curta}</p>
              <dl class="service-detail__meta">
                <div><dt>Preço</dt><dd class="service-card__price">${formatPrice(servico.preco)}</dd></div>
                <div><dt>Duração</dt><dd>${formatDuration(servico.duracao_minutos)}</dd></div>
              </dl>
              <div class="service-detail__text">
                ${paragrafos.length ? paragrafos.map((p) => html`<p>${p}</p>`) : html`<p>${servico.descricao_curta}</p>`}
              </div>
              <div class="service-detail__actions">
                ${whatsappButton({
                  numero: loja?.numero_whatsapp,
                  mensagem: buildServiceMessage(servico.nome, loja?.nome_da_barbearia),
                  rotulo: loja?.texto_botao_principal || 'Agendar pelo WhatsApp',
                  classe: 'btn btn--primary btn--lg',
                })}
                <a class="btn btn--ghost" href="/servicos">Voltar aos serviços</a>
              </div>
            </div>
          </article>
        </div>`,
      );
    } catch (erro) {
      if (signal.aborted || erro?.name === 'AbortError') return;
      const contenedor = root;
      if (erro?.status === 404) {
        ctx.setTitle('Serviço não encontrado');
        setHtml(
          contenedor,
          html`<div class="container page">${EmptyState({
            titulo: 'Serviço não encontrado',
            mensagem: 'Este serviço não existe ou não está disponível no momento.',
            acao: { href: '/servicos', rotulo: 'Ver todos os serviços' },
          })}</div>`,
        );
        return;
      }
      setHtml(contenedor, html`<div class="container page" data-erro></div>`);
      renderError(contenedor.querySelector('[data-erro]'), erro, carregar, 'Não foi possível carregar o serviço');
    }
  };

  await carregar();
  return () => {};
}