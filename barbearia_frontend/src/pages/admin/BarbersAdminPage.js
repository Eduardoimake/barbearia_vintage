/**
 * CRUD de barbeiros (/painel/barbeiros). Upload via FormData em foto_principal.
 */
import { html, setHtml } from '../../utils/dom.js';
import { barbersApi } from '../../api/adminApi.js';
import { updateQuery } from '../../router.js';
import { clearPublicCache } from '../../state/appState.js';
import { getErrorMessage } from '../../utils/errors.js';
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

/** Definição dos campos (nomes exatos do contrato). */
const CAMPOS = [
  { name: 'nome', label: 'Nome', type: 'text', required: true },
  { name: 'slug', label: 'Slug (endereço)', type: 'text', omitirSeVazio: true, ajuda: 'Opcional. Se vazio na criação, é gerado a partir do nome.' },
  { name: 'especialidade', label: 'Especialidade', type: 'text', required: true },
  { name: 'descricao_curta', label: 'Descrição curta', type: 'textarea', rows: 3, required: true },
  { name: 'foto_principal', label: 'Foto principal', type: 'image' },
  { name: 'alt_text', label: 'Texto alternativo da foto', type: 'text', ajuda: 'Descreva a foto para leitores de tela.' },
  { name: 'ordem_exibicao', label: 'Ordem de exibição', type: 'number', min: 0, omitirSeVazio: true },
  { name: 'ativo', label: 'Barbeiro ativo (visível no site)', type: 'checkbox' },
];

/**
 * Renderiza o CRUD de barbeiros.
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
        <h1 class="admin-title" id="titulo-pagina" tabindex="-1">Barbeiros</h1>
        <button type="button" class="btn btn--primary" data-action="nova">Novo barbeiro</button>
      </header>
      <section class="admin-panel" data-painel aria-labelledby="titulo-form" hidden></section>
      <div data-tabela></div>
      <div data-paginacao></div>
    </div>`,
  );
  const painel = root.querySelector('[data-painel]');
  const tabela = root.querySelector('[data-tabela]');
  const paginacao = root.querySelector('[data-paginacao]');
  const botaoNovo = root.querySelector('[data-action="nova"]');

  /** Fecha o painel do formulário. */
  const fecharForm = () => {
    emEdicao = null;
    setHtml(painel, html``);
    painel.hidden = true;
  };

  /**
   * Abre o formulário para criar ou editar.
   * @param {object|null} item Barbeiro em edição (null = novo).
   */
  const abrirForm = (item) => {
    emEdicao = item;
    const valores = item || { ativo: true };
    setHtml(
      painel,
      html`<h2 id="titulo-form" class="admin-panel__title">${item ? `Editar barbeiro: ${item.nome}` : 'Novo barbeiro'}</h2>
        ${AdminForm({ id: 'form-barbeiro', campos: CAMPOS, valores, enviar: item ? 'Salvar alterações' : 'Criar barbeiro' })}`,
    );
    painel.hidden = false;
    bindImageFields(painel);

    const formulario = painel.querySelector('#form-barbeiro');
    formulario.querySelector('.form-actions').insertAdjacentHTML('beforeend', '<button type="button" class="btn btn--ghost" data-action="cancelar-form">Cancelar</button>');
    formulario.querySelector('[data-action="cancelar-form"]').addEventListener('click', () => {
      fecharForm();
      botaoNovo.focus();
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
        if (item) await barbersApi.update(item.id, corpo);
        else await barbersApi.create(corpo);
        clearPublicCache();
        showToast(item ? 'Barbeiro atualizado com sucesso.' : 'Barbeiro criado com sucesso.', 'success');
        fecharForm();
        await carregar();
        botaoNovo.focus();
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
    setHtml(tabela, LoadingState('Carregando barbeiros...'));
    try {
      const resposta = await barbersApi.list({ page: estado.page, page_size: TAMANHO_PAGINA }, signal);
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
          legenda: 'Lista de barbeiros',
          vazio: 'Nenhum barbeiro cadastrado ainda.',
          linhas: itens,
          colunas: [
            {
              rotulo: 'Foto',
              render: (b) => {
                const url = resolveImageUrl(b.foto_principal);
                return url ? html`<img class="admin-thumb" src="${url}" alt="" loading="lazy" />` : html`<span class="muted">Sem foto</span>`;
              },
            },
            { rotulo: 'Barbeiro', render: (b) => html`<strong>${b.nome}</strong><br /><span class="muted">/${b.slug}</span>` },
            { rotulo: 'Especialidade', render: (b) => b.especialidade },
            { rotulo: 'Ordem', render: (b) => b.ordem_exibicao ?? '—' },
            {
              rotulo: 'Status',
              render: (b) => html`<span class="badge ${b.ativo ? 'badge--ok' : 'badge--off'}">${b.ativo ? 'Ativo' : 'Inativo'}</span>`,
            },
          ],
          acoes: (b) => html`<button type="button" class="btn btn--ghost btn--sm" data-action="editar" data-id="${b.id}" aria-label="Editar ${b.nome}">Editar</button>
            <button type="button" class="btn btn--danger btn--sm" data-action="excluir" data-id="${b.id}" aria-label="Excluir ${b.nome}">Excluir</button>`,
        }),
      );
      setHtml(paginacao, Pagination({ page: estado.page, count: resposta.count, pageSize: TAMANHO_PAGINA, rotulo: 'Paginação dos barbeiros' }));
    } catch (erro) {
      if (signal.aborted || erro?.name === 'AbortError') return;
      renderError(tabela, erro, carregar, 'Não foi possível carregar os barbeiros');
    }
  };

  botaoNovo.addEventListener('click', () => abrirForm(null));

  tabela.addEventListener('click', async (evento) => {
    const botao = evento.target instanceof Element ? evento.target.closest('button[data-action]') : null;
    if (!botao) return;
    const id = Number(botao.dataset.id);
    const barbeiro = itens.find((b) => b.id === id);
    if (!barbeiro) return;

    if (botao.dataset.action === 'editar') {
      abrirForm(barbeiro);
      return;
    }

    if (botao.dataset.action === 'excluir') {
      const confirmado = await confirmDialog({
        titulo: 'Excluir barbeiro',
        mensagem: `Deseja excluir o barbeiro "${barbeiro.nome}"? Esta ação não pode ser desfeita.`,
        confirmar: 'Excluir',
        perigo: true,
      });
      if (!confirmado) return;
      try {
        await barbersApi.remove(id); // 204 No Content
        clearPublicCache();
        if (emEdicao?.id === id) fecharForm();
        showToast(`Barbeiro "${barbeiro.nome}" excluído.`, 'success');
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

  await carregar();
  return () => {};
}