/**
 * Configuração da barbearia (/painel/barbearia).
 * GET/PATCH /admin/store/. Upload via FormData em imagem_capa_banner.
 * Se o registro ainda não existir (404), o PATCH com todos os campos obrigatórios o cria,
 * conforme o contrato.
 */
import { html, setHtml } from '../../utils/dom.js';
import { getAdminStore, updateAdminStore } from '../../api/adminApi.js';
import { clearPublicCache } from '../../state/appState.js';
import { buildRequestBody, clearFieldErrors, showFieldErrors, applyApiError, setSubmitting } from '../../utils/forms.js';
import { normalizeWhatsAppNumber, isValidWhatsAppNumber, isDemoNumber } from '../../utils/whatsapp.js';
import { LoadingState } from '../../components/LoadingState.js';
import { renderError } from '../../components/ErrorState.js';
import { AdminForm, readForm } from '../../components/AdminForm.js';
import { bindImageFields } from '../../components/ImageField.js';
import { showToast } from '../../components/Toast.js';

/** Definição dos campos (nomes exatos do contrato). */
const CAMPOS = [
  { name: 'nome_da_barbearia', label: 'Nome da barbearia', type: 'text', required: true },
  { name: 'slogan', label: 'Slogan', type: 'text', required: true },
  { name: 'descricao_apresentacao', label: 'Descrição de apresentação', type: 'textarea', rows: 5, required: true },
  { name: 'numero_whatsapp', label: 'Número do WhatsApp', type: 'text', required: true, ajuda: 'Com DDI e DDD, apenas números. Exemplo: 5521988887777.' },
  { name: 'endereco_demo', label: 'Endereço', type: 'text', required: true },
  { name: 'horario_atendimento', label: 'Horário de atendimento', type: 'text', required: true },
  { name: 'imagem_capa_banner', label: 'Imagem de capa (banner)', type: 'image' },
  { name: 'texto_banner', label: 'Texto do banner', type: 'textarea', rows: 3, required: true },
  { name: 'texto_botao_principal', label: 'Texto do botão principal', type: 'text' },
];

/**
 * Renderiza a configuração da barbearia.
 * @param {object} ctx Contexto do roteador.
 * @returns {Promise<Function>} Função de limpeza.
 */
export async function render(ctx) {
  const { root, signal } = ctx;

  setHtml(
    root,
    html`<div class="admin-page">
      <header class="admin-page__header">
        <h1 class="admin-title" tabindex="-1">Configuração da barbearia</h1>
      </header>
      <div data-conteudo></div>
    </div>`,
  );
  const conteudo = root.querySelector('[data-conteudo]');

  /**
   * Desenha o formulário com os dados atuais.
   * @param {object|null} loja Registro existente (null = ainda não configurado).
   */
  const desenhar = (loja) => {
    const aviso = [];
    if (!loja) {
      aviso.push('A barbearia ainda não foi configurada. Preencha todos os campos obrigatórios para criar a configuração.');
    } else if (isDemoNumber(loja.numero_whatsapp)) {
      aviso.push('O número de WhatsApp atual é demonstrativo, por isso os botões de WhatsApp do site estão desativados. Informe o número real para ativá-los.');
    }

    setHtml(
      conteudo,
      html`${aviso.map((texto) => html`<p class="admin-note admin-note--warn" role="note">${texto}</p>`)}
        <div class="admin-panel">${AdminForm({
          id: 'form-loja',
          campos: CAMPOS,
          valores: loja || {},
          enviar: 'Salvar configuração',
        })}</div>`,
    );
    bindImageFields(conteudo);

    const formulario = conteudo.querySelector('#form-loja');
    formulario.addEventListener('submit', async (evento) => {
      evento.preventDefault();
      clearFieldErrors(formulario);

      const { valores, erros } = readForm(formulario, CAMPOS);
      if (valores.numero_whatsapp) {
        const digitos = normalizeWhatsAppNumber(valores.numero_whatsapp);
        if (!isValidWhatsAppNumber(digitos)) erros.numero_whatsapp = 'Informe de 10 a 15 dígitos, com DDI e DDD.';
        else valores.numero_whatsapp = digitos;
      }
      if (Object.keys(erros).length) {
        showFieldErrors(formulario, erros, 'Corrija os campos destacados.');
        return;
      }

      setSubmitting(formulario, true);
      try {
        const atualizado = await updateAdminStore(buildRequestBody(valores));
        clearPublicCache();
        showToast('Configuração da barbearia salva com sucesso.', 'success');
        desenhar(atualizado);
        conteudo.querySelector('#form-loja input')?.focus();
      } catch (erro) {
        if (signal.aborted) return;
        setSubmitting(formulario, false);
        applyApiError(formulario, erro);
      }
    });
  };

  const carregar = async () => {
    setHtml(conteudo, LoadingState('Carregando configuração...'));
    try {
      const loja = await getAdminStore(signal);
      if (signal.aborted) return;
      desenhar(loja);
    } catch (erro) {
      if (signal.aborted || erro?.name === 'AbortError') return;
      if (erro?.status === 404) {
        desenhar(null);
        return;
      }
      renderError(conteudo, erro, carregar, 'Não foi possível carregar a configuração');
    }
  };

  await carregar();
  return () => {};
}