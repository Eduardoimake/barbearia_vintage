/**
 * Lista administrativa de serviços (/painel/servicos):
 * listar, publicar/ocultar (PATCH status_published), editar e excluir.
 */
import { html, setHtml } from '../../utils/dom.js';
import { servicesApi, categoriesApi } from '../../api/adminApi.js';
import { updateQuery } from '../../router.js';
import { clearPublicCache } from '../../state/appState.js';
import { getErrorMessage } from '../../utils/errors.js';
import { formatPrice, formatDuration } from '../../utils/formatters.js';
import { resolveImageUrl } from '../../utils/imageUrl.js';
import { LoadingState } from '../../components/LoadingState.js';
import { renderError } from '../../components/ErrorState.js';
import { AdminTable } from '../../components/AdminTable.js';
import { Pagination, bindPagination } from '../../components/Pagination.js';
import { confirmDialog } from '../../components/ConfirmDialog.js';
import { showToast } from '../../components/Toast.js';

const TAMANHO_PAGINA = 10;

/**
 * Renderiza a lista de serviços do painel.
 * @param {object} ctx Contexto do roteador.
 * @returns {Promise<Function>} Função de limpeza.
 */
export async function render(ctx) {
  const { root, signal, query } = ctx;
  const estado = { page: Math.max(1, Number.parseInt(query.page, 10) || 1) };
  let itens = [];
  let mapaCategorias = new Map();

  setHtml(
    root,
    html`<div class="admin-page">
      <header class="admin-page__header">
        <h1 class="admin-title" id="titulo-pagina" tabindex="-1">Serviços</h1>
        <a class="btn btn--primary" href="/painel/servicos/novo">Novo serviço</a>
      </header>
      <div data-tabela></div>
      <div data-paginacao></div>
    </div>`,
  );
  const tabela = root.querySelector('[data-tabela]');
  const paginacao = root.querySelector('[data-paginacao]');

  /** Carrega e desenha a página atual. */
  const carregar = async () => {
    setHtml(tabela, LoadingState('Carregando serviços...'));
    try {
      const resposta = await servicesApi.list({ page: estado.page, page_size: TAMANHO_PAGINA }, signal);
      if (signal.aborted) return;

      // Página vazia após exclusões: volta para a última página existente
      if (!resposta.results.length && estado.page > 1 && resposta.count > 0) {
        estado.page = Math.ceil(resposta.count / TAMANHO_PAGINA);
        updateQuery({ page: estado.page > 1 ? estado.page : '' });
        await carregar();
        return;
      }

      itens = resposta.results;
      setHtml(
        tabela,
        AdminTable({
          legenda: 'Lista de serviços',
          vazio: 'Nenhum serviço cadastrado ainda. Use "Novo serviço" para começar.',
          linhas: itens,
          colunas: [
            {
              rotulo: 'Imagem',
              render: (s) => {
                const url = resolveImageUrl(s.imagem_principal);
                return url ? html`<img class="admin-thumb" src="${url}" alt="" loading="lazy" />` : html`<span class="muted">Sem imagem</span>`;
              },
            },
            { rotulo: 'Serviço', render: (s) => html`<strong>${s.nome}</strong><br /><span class="muted">/${s.slug}</span>` },
            { rotulo: 'Categoria', render: (s) => mapaCategorias.get(s.categoria) ?? `#${s.categoria}` },
            { rotulo: 'Preço', render: (s) => formatPrice(s.preco) },
            { rotulo: 'Duração', render: (s) => formatDuration(s.duracao_minutos) },
            { rotulo: 'Destaque', render: (s) => (s.destaque_pagina_inicial ? 'Sim' : 'Não') },
            {
              rotulo: 'Status',
              render: (s) => html`<span class="badge ${s.status_published ? 'badge--ok' : 'badge--off'}">${s.status_published ? 'Publicado' : 'Oculto'}</span>`,
            },
          ],
          acoes: (s) => html`<a class="btn btn--ghost btn--sm" href="/painel/servicos/${s.id}/editar" aria-label="Editar ${s.nome}">Editar</a>
            <button type="button" class="btn btn--ghost btn--sm" data-action="alternar" data-id="${s.id}" aria-label="${s.status_published ? 'Ocultar' : 'Publicar'} ${s.nome}">${s.status_published ? 'Ocultar' : 'Publicar'}</button>
            <button type="button" class="btn btn--danger btn--sm" data-action="excluir" data-id="${s.id}" aria-label="Excluir ${s.nome}">Excluir</button>`,
        }),
      );
      setHtml(paginacao, Pagination({ page: estado.page, count: resposta.count, pageSize: TAMANHO_PAGINA, rotulo: 'Paginação dos serviços' }));
    } catch (erro) {
      if (signal.aborted || erro?.name === 'AbortError') return;
      renderError(tabela, erro, carregar, 'Não foi possível carregar os serviços');
    }
  };

  /** Foca o título após uma ação que redesenha a tabela. */
  const focarTitulo = () => root.querySelector('#titulo-pagina')?.focus();

  tabela.addEventListener('click', async (evento) => {
    const botao = evento.target instanceof Element ? evento.target.closest('button[data-action]') : null;
    if (!botao) return;
    const id = Number(botao.dataset.id);
    const servico = itens.find((s) => s.id === id);
    if (!servico) return;

    if (botao.dataset.action === 'alternar') {
      const publicar = !servico.status_published;
      botao.disabled = true;
      try {
        await servicesApi.update(id, { json: { status_published: publicar } });
        clearPublicCache();
        showToast(publicar ? `"${servico.nome}" foi publicado.` : `"${servico.nome}" foi ocultado do site.`, 'success');
        await carregar();
        tabela.querySelector(`button[data-action="alternar"][data-id="${id}"]`)?.focus();
      } catch (erro) {
        botao.disabled = false;
        showToast(getErrorMessage(erro), 'error');
      }
      return;
    }

    if (botao.dataset.action === 'excluir') {
      const confirmado = await confirmDialog({
        titulo: 'Excluir serviço',
        mensagem: `Deseja excluir o serviço "${servico.nome}"? Esta ação não pode ser desfeita. Promoções vinculadas ficarão sem serviço.`,
        confirmar: 'Excluir',
        perigo: true,
      });
      if (!confirmado) return;
      try {
        await servicesApi.remove(id); // 204 No Content
        clearPublicCache();
        showToast(`Serviço "${servico.nome}" excluído.`, 'success');
        await carregar();
        focarTitulo();
      } catch (erro) {
        showToast(getErrorMessage(erro), 'error');
      }
    }
  });

  bindPagination(paginacao, (pagina) => {
    estado.page = pagina;
    updateQuery({ page: pagina > 1 ? pagina : '' });
    carregar().then(focarTitulo);
  });

  // Nomes das categorias (falha aqui não impede a lista)
  try {
    const categorias = await categoriesApi.listAll(signal);
    mapaCategorias = new Map(categorias.map((c) => [c.id, c.nome]));
  } catch {
    /* mantém o fallback "#id" */
  }
  if (signal.aborted) return () => {};

  await carregar();
  return () => {};
}