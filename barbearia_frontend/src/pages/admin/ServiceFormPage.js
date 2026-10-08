/**
 * Formulário de serviço: criação (/painel/servicos/novo) e edição
 * (/painel/servicos/:id/editar). Upload via FormData em imagem_principal.
 */
import { html, setHtml } from '../../utils/dom.js';
import { servicesApi, categoriesApi } from '../../api/adminApi.js';
import { clearPublicCache } from '../../state/appState.js';
import { getErrorMessage } from '../../utils/errors.js';
import { buildRequestBody, clearFieldErrors, showFieldErrors, applyApiError, setSubmitting } from '../../utils/forms.js';
import { LoadingState } from '../../components/LoadingState.js';
import { EmptyState } from '../../components/EmptyState.js';
import { renderError } from '../../components/ErrorState.js';
import { AdminForm, readForm } from '../../components/AdminForm.js';
import { bindImageFields } from '../../components/ImageField.js';
import { showToast } from '../../components/Toast.js';

/**
 * Renderiza o formulário de serviço.
 * @param {object} ctx Contexto do roteador.
 * @returns {Promise<Function>} Função de limpeza.
 */
export async function render(ctx) {
  const { root, params, signal, navigate } = ctx;
  const editando = Boolean(params.id);
  const titulo = editando ? 'Editar serviço' : 'Novo serviço';

  setHtml(
    root,
    html`<div class="admin-page">
      <header class="admin-page__header">
        <h1 class="admin-title" tabindex="-1">${titulo}</h1>
        <a class="btn btn--ghost" href="/painel/servicos">Voltar à lista</a>
      </header>
      <div data-conteudo></div>
    </div>`,
  );
  const conteudo = root.querySelector('[data-conteudo]');

  const carregar = async () => {
    setHtml(conteudo, LoadingState('Carregando formulário...'));
    try {
      const [categorias, servico] = await Promise.all([
        categoriesApi.listAll(signal),
        editando ? servicesApi.get(params.id, signal) : Promise.resolve(null),
      ]);
      if (signal.aborted) return;

      if (!categorias.length) {
        setHtml(
          conteudo,
          EmptyState({
            titulo: 'Cadastre uma categoria primeiro',
            mensagem: 'Todo serviço precisa pertencer a uma categoria.',
            acao: { href: '/painel/categorias', rotulo: 'Ir para categorias' },
          }),
        );
        return;
      }

      if (servico) ctx.setTitle(`Editar: ${servico.nome}`);

      const campos = [
        {
          name: 'categoria',
          label: 'Categoria',
          type: 'select',
          required: true,
          opcoes: categorias.map((c) => ({ valor: c.id, rotulo: c.ativa ? c.nome : `${c.nome} (inativa)` })),
          ajuda: 'Serviços de categorias inativas não aparecem no site.',
        },
        { name: 'nome', label: 'Nome', type: 'text', required: true },
        { name: 'slug', label: 'Slug (endereço)', type: 'text', omitirSeVazio: true, ajuda: 'Opcional. Se vazio na criação, é gerado a partir do nome.' },
        { name: 'descricao_curta', label: 'Descrição curta', type: 'textarea', rows: 2, required: true },
        { name: 'descricao_completa', label: 'Descrição completa', type: 'textarea', rows: 6, required: true },
        { name: 'preco', label: 'Preço (R$)', type: 'decimal', required: true, ajuda: 'Exemplo: 55.00 ou 55,00.' },
        { name: 'duracao_minutos', label: 'Duração (minutos)', type: 'number', required: true, min: 1 },
        { name: 'imagem_principal', label: 'Imagem principal', type: 'image' },
        { name: 'alt_text', label: 'Texto alternativo da imagem', type: 'text', ajuda: 'Descreva a imagem para leitores de tela.' },
        { name: 'destaque_pagina_inicial', label: 'Exibir em destaque na página inicial', type: 'checkbox' },
        { name: 'status_published', label: 'Publicado (visível no site)', type: 'checkbox', ajuda: 'Só aparece publicamente se a categoria também estiver ativa.' },
        { name: 'ordem_exibicao', label: 'Ordem de exibição', type: 'number', min: 0, omitirSeVazio: true },
      ];

      const valores = servico
        ? { ...servico, categoria: String(servico.categoria) }
        : { status_published: true, destaque_pagina_inicial: false };

      setHtml(
        conteudo,
        html`<div class="admin-panel">${AdminForm({
          id: 'form-servico',
          campos,
          valores,
          enviar: editando ? 'Salvar alterações' : 'Criar serviço',
          cancelarHref: '/painel/servicos',
        })}</div>`,
      );
      bindImageFields(conteudo);

      const formulario = conteudo.querySelector('#form-servico');
      formulario.addEventListener('submit', async (evento) => {
        evento.preventDefault();
        clearFieldErrors(formulario);

        const { valores: enviados, erros } = readForm(formulario, campos);
        if (Object.keys(erros).length) {
          showFieldErrors(formulario, erros, 'Corrija os campos destacados.');
          return;
        }
        if (enviados.categoria !== undefined && enviados.categoria !== null) {
          enviados.categoria = Number(enviados.categoria);
        }
        if (servico && enviados.slug === servico.slug) delete enviados.slug;

        setSubmitting(formulario, true);
        try {
          const corpo = buildRequestBody(enviados);
          if (servico) await servicesApi.update(servico.id, corpo);
          else await servicesApi.create(corpo);
          clearPublicCache();
          showToast(servico ? 'Serviço atualizado com sucesso.' : 'Serviço criado com sucesso.', 'success');
          navigate('/painel/servicos');
        } catch (erro) {
          if (signal.aborted) return;
          setSubmitting(formulario, false);
          applyApiError(formulario, erro);
        }
      });
    } catch (erro) {
      if (signal.aborted || erro?.name === 'AbortError') return;
      if (erro?.status === 404) {
        setHtml(
          conteudo,
          EmptyState({
            titulo: 'Serviço não encontrado',
            mensagem: getErrorMessage(erro),
            acao: { href: '/painel/servicos', rotulo: 'Voltar à lista' },
          }),
        );
        return;
      }
      renderError(conteudo, erro, carregar, 'Não foi possível carregar o formulário');
    }
  };

  await carregar();
  return () => {};
}