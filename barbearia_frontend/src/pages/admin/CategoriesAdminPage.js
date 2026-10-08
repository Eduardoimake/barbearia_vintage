/**
 * CRUD de categorias (/painel/categorias).
 * Exclusão de categoria com serviços retorna 409: a mensagem da API é exibida num alerta.
 */
import { html, setHtml } from '../../utils/dom.js';
import { categoriesApi } from '../../api/adminApi.js';
import { updateQuery } from '../../router.js';
import { clearPublicCache } from '../../state/appState.js';
import { getErrorMessage } from '../../utils/errors.js';
import { buildRequestBody, clearFieldErrors, showFieldErrors, applyApiError, setSubmitting } from '../../utils/forms.js';
import { LoadingState } from '../../components/LoadingState.js';
import { renderError } from '../../components/ErrorState.js';
import { AdminTable } from '../../components/AdminTable.js';
import { AdminForm, readForm } from '../../components/AdminForm.js';
import { Pagination, bindPagination } from '../../components/Pagination.js';
import { confirmDialog } from '../../components/ConfirmDialog.js';
import { showToast } from '../../components/Toast.js';

const TAMANHO_PAGINA = 10;

/** Definição dos campos (nomes exatos do contrato). */
const CAMPOS = [
  { name: 'nome', label: 'Nome', type: 'text', required: true },
  { name: 'slug', label: 'Slug (endereço)', type: 'text', omitirSeVazio: true, ajuda: 'Opcional. Se vazio na criação, é gerado a partir do nome.' },
  { name: 'descricao_curta', label: 'Descrição curta', type: 'textarea', rows: 3 },
  { name: 'ordem_exibicao', label: 'Ordem de exibição', type: 'number', min: 0, omitirSeVazio: true },
  { name: 'ativa', label: 'Categoria ativa (visível no site)', type: 'checkbox' },
];

/**
 * Renderiza o CRUD de categorias.
 * @param {object} ctx Contexto do roteador.
 * @returns {Promise<Function>} Função de limpeza.
 */
export async function render(ctx) {
  const { root, signal, query } = ctx;
  const estado = { page: Math.max(1, Number.parseInt(query.page, 10) || 1) };
  let itens = [];
  let emEdicao = null;

  setHtml(
    root,
    html`<div class="admin-page">
      <header class="admin-page__header">
        <h1 class="admin-title" id="titulo-pagina" tabindex="-1">Categorias</h1>
        <button type="button" class="btn btn--primary" data-action="nova">Nova categoria</button>
      </header>
      <div class="form-alert" data-aviso role="alert" tabindex="-1" hidden></div>
      <section class="admin-panel" data-painel aria-labelledby="titulo-form" hidden></section>
      <div data-tabela></div>
      <div data-paginacao></div>
    </div>`,
  );
  const aviso = root.querySelector('[data-aviso]');
  const painel = root.querySelector('[data-painel]');
  const tabela = root.querySelector('[data-tabela]');
  const paginacao = root.querySelector('[data-paginacao]');
  const botaoNova = root.querySelector('[data-action="nova"]');

  /** Exibe ou limpa o alerta geral da página. */
  const mostrarAviso = (mensagem) => {
    aviso.textContent = mensagem || '';
    aviso.hidden = !mensagem;
    if (mensagem) aviso.focus();
  };

  /** Fecha o painel do formulário. */
  const fecharForm = () => {
    emEdicao = null;
    setHtml(painel, html``);
    painel.hidden = true;
  };

  /**
   * Abre o formulário para criar ou editar.
   * @param {object|null} item Categoria em edição (null = nova).
   */
  const abrirForm = (item) => {
    emEdicao = item;
    mostrarAviso('');
    const valores = item || { ativa: true };
    setHtml(
      painel,
      html`<h2 id="titulo-form" class="admin-panel__title">${item ? `Editar categoria: ${item.nome}` : 'Nova categoria'}</h2>
        ${AdminForm({ id: 'form-categoria', campos: CAMPOS, valores, enviar: item ? 'Salvar alterações' : 'Criar categoria' })}`,
    );
    painel.hidden = false;
    const formulario = painel.querySelector('#form-categoria');
    formulario.querySelector('.form-actions').insertAdjacentHTML('beforeend', '<button type="button" class="btn btn--ghost" data-action="cancelar-form">Cancelar</button>');
    formulario.querySelector('[data-action="cancelar-form"]').addEventListener('click', () => {
      fecharForm();
      botaoNova.focus();
    });

    formulario.addEventListener('submit', async (evento) => {
      evento.preventDefault();
      clearFieldErrors(formulario);
      const { valores: enviados, erros } = readForm(formulario, CAMPOS);
      if (Object.keys(erros).length) {
        showFieldErrors(formulario, erros, 'Corrija os campos destacados.');
        return;
      }
      if (item && enviados.slug === item.slug) delete enviados.slug;

      setSubmitting(formulario, true);
      try {
        const corpo = buildRequestBody(enviados);
        if (item) await categoriesApi.update(item.id, corpo);
        else await categoriesApi.create(corpo);
        clearPublicCache();
        showToast(item ? 'Categoria atualizada com sucesso.' : 'Categoria criada com sucesso.', 'success');
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
    setHtml(tabela, LoadingState('Carregando categorias...'));
    try {
      const resposta = await categoriesApi.list({ page: estado.page, page_size: TAMANHO_PAGINA }, signal);
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
          legenda: 'Lista de categorias',
          vazio: 'Nenhuma categoria cadastrada ainda.',
          linhas: itens,
          colunas: [
            { rotulo: 'Categoria', render: (c) => html`<strong>${c.nome}</strong><br /><span class="muted">/${c.slug}</span>` },
            { rotulo: 'Descrição', render: (c) => c.descricao_curta || '—' },
            { rotulo: 'Ordem', render: (c) => c.ordem_exibicao ?? '—' },
            {
              rotulo: 'Status',
              render: (c) => html`<span class="badge ${c.ativa ? 'badge--ok' : 'badge--off'}">${c.ativa ? 'Ativa' : 'Inativa'}</span>`,
            },
          ],
          acoes: (c) => html`<button type="button" class="btn btn--ghost btn--sm" data-action="editar" data-id="${c.id}" aria-label="Editar categoria ${c.nome}">Editar</button>
            <button type="button" class="btn btn--danger btn--sm" data-action="excluir" data-id="${c.id}" aria-label="Excluir categoria ${c.nome}">Excluir</button>`,
        }),
      );
      setHtml(paginacao, Pagination({ page: estado.page, count: resposta.count, pageSize: TAMANHO_PAGINA, rotulo: 'Paginação das categorias' }));
    } catch (erro) {
      if (signal.aborted || erro?.name === 'AbortError') return;
      renderError(tabela, erro, carregar, 'Não foi possível carregar as categorias');
    }
  };

  botaoNova.addEventListener('click', () => abrirForm(null));

  tabela.addEventListener('click', async (evento) => {
    const botao = evento.target instanceof Element ? evento.target.closest('button[data-action]') : null;
    if (!botao) return;
    const id = Number(botao.dataset.id);
    const categoria = itens.find((c) => c.id === id);
    if (!categoria) return;

    if (botao.dataset.action === 'editar') {
      abrirForm(categoria);
      return;
    }

    if (botao.dataset.action === 'excluir') {
      mostrarAviso('');
      const confirmado = await confirmDialog({
        titulo: 'Excluir categoria',
        mensagem: `Deseja excluir a categoria "${categoria.nome}"? Esta ação não pode ser desfeita.`,
        confirmar: 'Excluir',
        perigo: true,
      });
      if (!confirmado) return;
      try {
        await categoriesApi.remove(id); // 204 No Content
        clearPublicCache();
        if (emEdicao?.id === id) fecharForm();
        showToast(`Categoria "${categoria.nome}" excluída.`, 'success');
        await carregar();
        root.querySelector('#titulo-pagina')?.focus();
      } catch (erro) {
        if (erro?.status === 409) {
          // Categoria com serviços vinculados
          mostrarAviso(`${getErrorMessage(erro)} Exclua ou mova esses serviços para outra categoria e tente novamente.`);
        } else {
          showToast(getErrorMessage(erro), 'error');
        }
      }
    }
  });

  bindPagination(paginacao, (pagina) => {
    estado.page = pagina;
    updateQuery({ page: pagina > 1 ? pagina : '' });
    carregar().then(() => root.querySelector('#titulo-pagina')?.focus());
  });

  await carregar();
  return () => {};
}