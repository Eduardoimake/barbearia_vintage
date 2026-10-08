/**
 * Utilitários de formulário: corpo da requisição (JSON ou FormData),
 * validação de imagem, erros por campo acessíveis e estado de envio.
 */
import { ApiError, getErrorMessage, parseValidationErrors } from './errors.js';

export const TIPOS_IMAGEM = ['image/jpeg', 'image/png', 'image/webp'];
export const TAMANHO_MAX_BYTES = 5 * 1024 * 1024; // 5 MB (limite do backend)

/**
 * Valida o arquivo de imagem no cliente (o backend continua sendo a autoridade).
 * @param {File|null|undefined} arquivo
 * @returns {string|null} Mensagem de erro ou null se válido.
 */
export function validateImageFile(arquivo) {
  if (!arquivo) return null;
  if (!TIPOS_IMAGEM.includes(arquivo.type)) {
    return 'Formato inválido. Use JPEG, PNG ou WebP.';
  }
  if (arquivo.size > TAMANHO_MAX_BYTES) {
    return 'A imagem excede o limite de 5 MB.';
  }
  return null;
}

/**
 * Monta o corpo da requisição.
 * Com arquivo: FormData (booleanos e números como string; nulos como "").
 * Sem arquivo: JSON.
 * @param {Record<string, any>} campos Valores já normalizados.
 * @returns {{formData: FormData}|{json: object}}
 */
export function buildRequestBody(campos) {
  const temArquivo = Object.values(campos).some((v) => v instanceof File);
  if (!temArquivo) {
    const json = {};
    for (const [chave, valor] of Object.entries(campos)) {
      if (valor !== undefined) json[chave] = valor;
    }
    return { json };
  }

  const formData = new FormData();
  for (const [chave, valor] of Object.entries(campos)) {
    if (valor === undefined) continue;
    if (valor instanceof File) formData.append(chave, valor);
    else if (valor === null) formData.append(chave, '');
    else if (typeof valor === 'boolean') formData.append(chave, valor ? 'true' : 'false');
    else formData.append(chave, String(valor));
  }
  return { formData };
}

/**
 * Remove mensagens de erro anteriores do formulário e restaura o aria-describedby original.
 * @param {HTMLFormElement} formulario
 */
export function clearFieldErrors(formulario) {
  formulario.querySelectorAll('[aria-invalid="true"]').forEach((el) => {
    el.removeAttribute('aria-invalid');
  });
  formulario.querySelectorAll('[data-ajuda-id]').forEach((el) => {
    const original = el.dataset.ajudaId;
    if (original) el.setAttribute('aria-describedby', original);
    else el.removeAttribute('aria-describedby');
    delete el.dataset.ajudaId;
  });
  formulario.querySelectorAll('.field-error').forEach((el) => el.remove());
  const alerta = formulario.querySelector('[data-form-alert]');
  if (alerta) {
    alerta.textContent = '';
    alerta.hidden = true;
  }
}

/**
 * Exibe erros por campo e um alerta geral. Move o foco ao primeiro erro.
 * @param {HTMLFormElement} formulario
 * @param {Record<string,string>} campos Erros por nome de campo.
 * @param {string} [geral] Mensagem geral.
 */
export function showFieldErrors(formulario, campos, geral = '') {
  const semCampo = [];
  let primeiro = null;

  for (const [nome, mensagem] of Object.entries(campos)) {
    const entrada = formulario.querySelector(`[name="${CSS.escape(nome)}"]`);
    if (!entrada) {
      semCampo.push(mensagem);
      continue;
    }
    entrada.setAttribute('aria-invalid', 'true');
    const idErro = `${entrada.id || nome}-erro`;
    const erro = document.createElement('p');
    erro.className = 'field-error';
    erro.id = idErro;
    erro.textContent = mensagem; // textContent: sem risco de injeção
    const alvo = entrada.closest('.form-field') || entrada.parentElement;
    alvo.appendChild(erro);

    if (!('ajudaId' in entrada.dataset)) {
      entrada.dataset.ajudaId = entrada.getAttribute('aria-describedby') || '';
    }
    entrada.setAttribute('aria-describedby', `${idErro} ${entrada.dataset.ajudaId}`.trim());
    if (!primeiro) primeiro = entrada;
  }

  const textoGeral = [geral, ...semCampo].filter(Boolean).join(' ');
  const alerta = formulario.querySelector('[data-form-alert]');
  if (alerta && textoGeral) {
    alerta.textContent = textoGeral;
    alerta.hidden = false;
    if (!primeiro) alerta.focus();
  }
  if (primeiro) primeiro.focus();
}

/**
 * Traduz um erro da API para a interface do formulário:
 * 400 -> erros por campo; demais status -> alerta geral em português.
 * @param {HTMLFormElement} formulario
 * @param {unknown} erro
 */
export function applyApiError(formulario, erro) {
  clearFieldErrors(formulario);
  if (erro instanceof ApiError && erro.status === 400) {
    const { fields, general } = parseValidationErrors(erro.data);
    const geral = Object.keys(fields).length || general ? general : getErrorMessage(erro);
    showFieldErrors(formulario, fields, geral || 'Revise os campos destacados.');
    return;
  }
  showFieldErrors(formulario, {}, getErrorMessage(erro));
}

/**
 * Alterna o estado "enviando" do botão de envio (data-submit).
 * @param {HTMLFormElement} formulario
 * @param {boolean} ocupado
 * @param {string} [rotuloOcupado]
 */
export function setSubmitting(formulario, ocupado, rotuloOcupado = 'Salvando...') {
  const botao = formulario.querySelector('[data-submit]');
  if (!botao) return;
  if (ocupado) {
    botao.dataset.rotuloOriginal = botao.textContent;
    botao.textContent = rotuloOcupado;
    botao.disabled = true;
    formulario.setAttribute('aria-busy', 'true');
  } else {
    if (botao.dataset.rotuloOriginal) botao.textContent = botao.dataset.rotuloOriginal;
    botao.disabled = false;
    formulario.removeAttribute('aria-busy');
  }
}