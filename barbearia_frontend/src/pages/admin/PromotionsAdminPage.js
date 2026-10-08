/**
 * CRUD de promoções (/painel/promocoes). Upload via FormData em imagem.
 * No admin, servico_vinculado é o ID do serviço (ou null).
 */
import { html, setHtml } from '../../utils/dom.js';
import { promotionsApi, servicesApi } from '../../api/adminApi.js';
import { updateQuery } from '../../router.js';
import { clearPublicCache } from '../../state/appState.js';
import { getErrorMessage } from '../../utils/errors.js';
import { formatDate, toDatetimeLocal } from '../../utils/formatters.js';
import { resolveImageUrl } from '../../utils/imageUrl.js';
import { buildRequestBody, clearFieldErrors, showFieldErrors, applyApiError, setSubmitting } from '../../utils/forms.js';
import { LoadingState } from '../../components/LoadingState.js';
import { renderError } from '../../components/ErrorState.js';
import { AdminTable } from '../../components/AdminTable.js';
import { AdminForm, readForm } from '../../components/AdminForm.js';
import { bindImageFields } from '../../components/ImageField.js';
import { Pagination, bindPagination } from '../../components/Pagination.js';
import { confirmDialog } from '../../components/ConfirmDialog.js';
import { showToast } from '../../components/Toast.js';

const TAMANHO_PAGINA = 10;

/**
 * Renderiza o CRUD de promoções.
 * @param {object} ctx Contexto do roteador.
 * @returns {Promise<Function>} Função de limpeza.
 */
export async function render(ctx) {
  const { root, signal, query } = ctx;
  const estado = { page: Math.max(1, Number.parseInt(query.page, 10) || 1) };
  let itens = [];
  let emEdicao = null;
  let servicos = [];
  let mapaServicos = new Map();

  setHtml(
    root,
    html`<div class="admin-page">
      <header class="admin-page__header">
        <h1 class="admin-title" id="titulo-pagina" tabindex="-1">Promoções</h1>
        <button type="button" class="btn btn--primary" data-action="nova">Nova promoção</button>
      </header>
      <section class="admin-panel" data-painel aria-labelledby="titulo-form" hidden></section>
      <div data-tabela></div>
      <div data-paginacao></div>
    </div>`,
  );
  const painel = root.querySelector('[data-painel]');
  const tabela = root.querySelector('[data-tabela]');
  const paginacao = root.querySelector('[data-paginacao]');
  const botaoNova = root.querySelector('[data-action="nova"]');

  /**
   * Monta a definição dos campos (as opções de serviço vêm da API).
   * @returns {object[]}
   */
  const montarCampos = () => [
    { name: 'titulo', label: 'Título', type: 'text', required: true },
    { name: 'descricao', label: 'Descrição', type: 'textarea', rows: 4, required: true },
    { name: 'imagem', label: 'Imagem da promoção', type: 'image' },
    {
      name: 'servico_vinculado',
      label: 'Serviço vinculado',
      type: 'select',
      placeholder: 'Nenhum serviço vinculado',
      opcoes: servicos.map((s) => ({ valor: s.id, rotulo: s.nome })),
      ajuda: 'Opcional. A promoção só aparece no site se o serviço estiver publicado.',
    },
    { name: 'data_inicio', label: 'Início da promoção', type: 'datetime', ajuda: 'Opcional. Vazio = já vigente.' },
    { name: 'data_fim', label: 'Fim da promoção', type: 'datetime', ajuda: 'Opcional. Vazio = sem data final.' },
    { name: 'ativa', label: 'Promoção ativa', type: 'checkbox' },
    { name: 'ordem_exibicao', label: 'Ordem de exibição', type: 'number', min: 0, omitirSeVazio: true },
  ];

  /** Fecha o painel do formulário. */
  const fecharForm = () => {
    emEdicao = null;
    setHtml(painel, html``);
    painel.hidden = true;
  };

  /**
   * Abre o formulário para criar ou editar.
   * @param {object|null} item Promoção em edição (null = nova).
   */
  const abrirForm = (item) => {
    emEdicao = item;
    const campos = montarCampos();
    const valores = item
      ? {
          ...item,
          servico_vinculado: item.servico_vinculado === null ? '' : String(item.servico_vinculado),
          data_inicio: toDatetimeLocal(item.data_inicio),
          data_fim: toDatetimeLocal(item.data_fim),
        }
      : { ativa: true };

    setHtml(
      painel,
      html`<h2 id="titulo-form" class="admin-panel__title">${item ? `Editar promoção: ${item.titulo}` : 'Nova promoção'}</h2>
        ${AdminForm({ id: 'form-promocao', campos, valores, enviar: item ? 'Salvar alterações' : 'Criar promoção' })}`,
    );
    painel.hidden = false;
    bindImageFields(painel);

    const formulario = painel.querySelector('#form-promocao');
    formulario.querySelector('.form-actions').insertAdjacentHTML('beforeend', '<button type="button" class="btn btn--ghost" data-action="cancelar-form">Cancelar</button>');
    formulario.querySelector('[data-action="cancelar-form"]').addEventListener('click', () => {
      fecharForm();
      botaoNova.focus();
    });

    formulario.addEventListener('submit', async (evento) => {
      evento.preventDefault();
      clearFieldErrors(formulario);
      const { valores: enviados, erros } = readForm(formulario, campos);
      if (Object.keys(erros).length) {
        showFieldErrors(formulario, erros, 'Corrija os campos destacados.');
        return;
      }
      if (enviados.servico_vinculado) enviados.servico_vinculado = Number(enviados.servico_vinculado);

      setSubmitting(formulario, true);
      try {
        const corpo = buildRequestBody(enviados);
        if (item) await promotionsApi.update(item.id, corpo);
        else await promotionsApi.create(corpo);
        clearPublicCache();
        showToast(item ? 'Promoção atualizada com sucesso.' : 'Promoção criada com sucesso.', 'success');
        fecharForm();
        await carregar();
        botaoNova.focus();
      } catch (erro) {
        if (signal.aborted) return;
        setSubmitting(formulario, false);
        applyApiError(formulario, erro);
      }
    });

    painel.scrollIntoView();
    formulario.querySelector('input, select, textarea')?.focus({ preventScroll: true });
  };

  /** Carrega e desenha a página atual. */
  const carregar = async () => {
    setHtml(tabela, LoadingState('Carregando promoções...'));
    try {
      const resposta = await promotionsApi.list({ page: estado.page, page_size: TAMANHO_PAGINA }, signal);
      if (signal.aborted) return;

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
          legenda: 'Lista de promoções',
          vazio: 'Nenhuma promoção cadastrada ainda.',
          linhas: itens,
          colunas: [
            {
              rotulo: 'Imagem',
              render: (p) => {
                const url = resolveImageUrl(p.imagem);
                return url ? html`<img class="admin-thumb" src="${url}" alt="" loading="lazy" />` : html`<span class="muted">Sem imagem</span>`;
              },
            },
            { rotulo: 'Promoção', render: (p) => html`<strong>${p.titulo}</strong>` },
            {
              rotulo: 'Serviço',
              render: (p) => (p.servico_vinculado === null ? 'Nenhum' : mapaServicos.get(p.servico_vinculado) ?? `#${p.servico_vinculado}`),
            },
            {
              rotulo: 'Período',
              render: (p) => `${p.data_inicio ? formatDate(p.data_inicio) : 'Já vigente'} → ${p.data_fim ? formatDate(p.data_fim) : 'Sem fim'}`,
            },
            {
              rotulo: 'Status',
              render: (p) => html`<span class="badge ${p.ativa ? 'badge--ok' : 'badge--off'}">${p.ativa ? 'Ativa' : 'Inativa'}</span>`,
            },
          ],
          acoes: (p) => html`<button type="button" class="btn btn--ghost btn--sm" data-action="editar" data-id="${p.id}" aria-label="Editar ${p.titulo}">Editar</button>
            <button type="button" class="btn btn--danger btn--sm" data-action="excluir" data-id="${p.id}" aria-label="Excluir ${p.titulo}">Excluir</button>`,
        }),
      );
      setHtml(paginacao, Pagination({ page: estado.page, count: resposta.count, pageSize: TAMANHO_PAGINA, rotulo: 'Paginação das promoções' }));
    } catch (erro) {
      if (signal.aborted || erro?.name === 'AbortError') return;
      renderError(tabela, erro, carregar, 'Não foi possível carregar as promoções');
    }
  };

  botaoNova.addEventListener('click', () => abrirForm(null));

  tabela.addEventListener('click', async (evento) => {
    const botao = evento.target instanceof Element ? evento.target.closest('button[data-action]') : null;
    if (!botao) return;
    const id = Number(botao.dataset.id);
    const promocao = itens.find((p) => p.id === id);
    if (!promocao) return;

    if (botao.dataset.action === 'editar') {
      abrirForm(promocao);
      return;
    }

    if (botao.dataset.action === 'excluir') {
      const confirmado = await confirmDialog({
        titulo: 'Excluir promoção',
        mensagem: `Deseja excluir a promoção "${promocao.titulo}"? O serviço vinculado não será afetado.`,
        confirmar: 'Excluir',
        perigo: true,
      });
      if (!confirmado) return;
      try {
        await promotionsApi.remove(id); // 204 No Content
        clearPublicCache();
        if (emEdicao?.id === id) fecharForm();
        showToast(`Promoção "${promocao.titulo}" excluída.`, 'success');
        await carregar();
        root.querySelector('#titulo-pagina')?.focus();
      } catch (erro) {
        showToast(getErrorMessage(erro), 'error');
      }
    }
  });

  bindPagination(paginacao, (pagina) => {
    estado.page = pagina;
    updateQuery({ page: pagina > 1 ? pagina : '' });
    carregar().then(() => root.querySelector('#titulo-pagina')?.focus());
  });

  // Serviços para o select e para a coluna "Serviço" (falha não impede a lista)
  try {
    servicos = await servicesApi.listAll(signal);
    mapaServicos = new Map(servicos.map((s) => [s.id, s.nome]));
  } catch {
    servicos = [];
  }
  if (signal.aborted) return () => {};

  await carregar();
  return () => {};
}