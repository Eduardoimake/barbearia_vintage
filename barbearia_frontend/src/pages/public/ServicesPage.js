/**
 * Lista de serviços (/servicos) com busca, filtro por categoria,
 * ordenação e paginação. Os filtros ficam na URL (search, category, ordering, page).
 * Parâmetros enviados exatamente como no contrato: search, category, ordering, page, page_size.
 */
import { html, setHtml, debounce } from '../../utils/dom.js';
import * as publicApi from '../../api/publicApi.js';
import { getStoreConfig, getPublicCategories } from '../../state/appState.js';
import { updateQuery } from '../../router.js';
import { LoadingState } from '../../components/LoadingState.js';
import { EmptyState } from '../../components/EmptyState.js';
import { renderError } from '../../components/ErrorState.js';
import { ServiceCard } from '../../components/ServiceCard.js';
import { Pagination, bindPagination } from '../../components/Pagination.js';

const TAMANHO_PAGINA = 12;

/** Opções de ordenação aceitas pela API. */
const ORDENACOES = [
  { valor: '', rotulo: 'Ordem padrão' },
  { valor: 'name', rotulo: 'Nome (A–Z)' },
  { valor: '-name', rotulo: 'Nome (Z–A)' },
  { valor: 'price', rotulo: 'Menor preço' },
  { valor: '-price', rotulo: 'Maior preço' },
];

/**
 * Renderiza a página de serviços.
 * @param {object} ctx Contexto do roteador.
 * @returns {Promise<Function>} Função de limpeza.
 */
export async function render(ctx) {
  const { root, signal, query } = ctx;

  const estado = {
    search: query.search || '',
    category: query.category || '',
    ordering: ORDENACOES.some((o) => o.valor === query.ordering) ? query.ordering || '' : '',
    page: Math.max(1, Number.parseInt(query.page, 10) || 1),
  };

  setHtml(
    root,
    html`<div class="container page">
      <header class="page-header">
        <h1 class="page-title">Serviços</h1>
        <p class="page-subtitle">Cuidado, técnica e personalidade em cada atendimento.</p>
      </header>

      <form class="filters" role="search" aria-label="Filtrar serviços" data-filtros>
        <div class="form-field">
          <label for="filtro-busca">Buscar serviço</label>
          <input type="search" id="filtro-busca" name="search" value="${estado.search}" autocomplete="off" placeholder="Ex.: barba" />
        </div>
        <div class="form-field">
          <label for="filtro-categoria">Categoria</label>
          <select id="filtro-categoria" name="category"><option value="">Todas as categorias</option></select>
        </div>
        <div class="form-field">
          <label for="filtro-ordem">Ordenar por</label>
          <select id="filtro-ordem" name="ordering">
            ${ORDENACOES.map((o) => html`<option value="${o.valor}" ${o.valor === estado.ordering ? html`selected` : ''}>${o.rotulo}</option>`)}
          </select>
        </div>
        <button type="button" class="btn btn--ghost btn--sm" data-action="limpar">Limpar filtros</button>
      </form>

      <h2 class="sr-only" id="resultados-titulo" tabindex="-1">Resultados</h2>
      <p class="results-summary" aria-live="polite" data-resumo></p>
      <div data-lista></div>
      <div data-paginacao></div>
    </div>`,
  );

  const formulario = root.querySelector('[data-filtros]');
  const campoBusca = root.querySelector('#filtro-busca');
  const campoCategoria = root.querySelector('#filtro-categoria');
  const campoOrdem = root.querySelector('#filtro-ordem');
  const resumo = root.querySelector('[data-resumo]');
  const lista = root.querySelector('[data-lista]');
  const paginacao = root.querySelector('[data-paginacao]');

  let controlador = null;
  let numeroRequisicao = 0;
  const lojaSegura = getStoreConfig().catch(() => null);

  /** Mantém a URL sincronizada com os filtros. */
  const sincronizarUrl = () => {
    updateQuery({
      search: estado.search,
      category: estado.category,
      ordering: estado.ordering,
      page: estado.page > 1 ? estado.page : '',
    });
  };

  /** Busca e desenha os serviços conforme o estado atual. */
  const carregar = async () => {
    if (controlador) controlador.abort();
    controlador = new AbortController();
    signal.addEventListener('abort', () => controlador.abort(), { once: true });
    numeroRequisicao += 1;
    const atual = numeroRequisicao;

    resumo.textContent = '';
    setHtml(paginacao, html``);
    setHtml(lista, LoadingState('Carregando serviços...'));

    try {
      const [resposta, loja] = await Promise.all([
        publicApi.getServices(
          {
            search: estado.search.trim(),
            category: estado.category,
            ordering: estado.ordering,
            page: estado.page,
            page_size: TAMANHO_PAGINA,
          },
          controlador.signal,
        ),
        lojaSegura,
      ]);
      if (signal.aborted || atual !== numeroRequisicao) return;

      resumo.textContent = `${resposta.count} ${resposta.count === 1 ? 'serviço encontrado' : 'serviços encontrados'}`;

      if (!resposta.results.length) {
        setHtml(lista, EmptyState({ titulo: 'Nenhum serviço encontrado', mensagem: 'Tente outro termo de busca ou limpe os filtros.' }));
        return;
      }
      setHtml(lista, html`<div class="grid grid--cards">${resposta.results.map((s) => ServiceCard(s, loja))}</div>`);
      setHtml(paginacao, Pagination({ page: estado.page, count: resposta.count, pageSize: TAMANHO_PAGINA, rotulo: 'Paginação dos serviços' }));
    } catch (erro) {
      if (signal.aborted || atual !== numeroRequisicao || erro?.name === 'AbortError') return;
      renderError(lista, erro, carregar, 'Não foi possível carregar os serviços');
    }
  };

  // Categorias para o filtro (falha aqui não impede a lista)
  getPublicCategories()
    .then((categorias) => {
      if (signal.aborted) return;
      setHtml(
        campoCategoria,
        html`<option value="">Todas as categorias</option>
        ${categorias.map((c) => html`<option value="${c.slug}" ${c.slug === estado.category ? html`selected` : ''}>${c.nome}</option>`)}`,
      );
    })
    .catch(() => {});

  const buscarComAtraso = debounce(() => {
    if (signal.aborted) return;
    estado.search = campoBusca.value;
    estado.page = 1;
    sincronizarUrl();
    carregar();
  }, 400);

  campoBusca.addEventListener('input', buscarComAtraso);
  formulario.addEventListener('submit', (e) => e.preventDefault());

  campoCategoria.addEventListener('change', () => {
    estado.category = campoCategoria.value;
    estado.page = 1;
    sincronizarUrl();
    carregar();
  });

  campoOrdem.addEventListener('change', () => {
    estado.ordering = campoOrdem.value;
    estado.page = 1;
    sincronizarUrl();
    carregar();
  });

  formulario.querySelector('[data-action="limpar"]').addEventListener('click', () => {
    estado.search = '';
    estado.category = '';
    estado.ordering = '';
    estado.page = 1;
    campoBusca.value = '';
    campoCategoria.value = '';
    campoOrdem.value = '';
    sincronizarUrl();
    carregar();
    campoBusca.focus();
  });

  bindPagination(paginacao, (pagina) => {
    estado.page = pagina;
    sincronizarUrl();
    carregar().then(() => {
      const titulo = root.querySelector('#resultados-titulo');
      if (titulo) {
        titulo.scrollIntoView();
        titulo.focus({ preventScroll: true });
      }
    });
  });

  await carregar();

  return () => {
    if (controlador) controlador.abort();
  };
}