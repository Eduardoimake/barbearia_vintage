/**
 * Geração de links do WhatsApp (wa.me).
 * O número fictício do seed nunca gera link ativo, conforme o contrato.
 */
import { html } from './dom.js';

/** Número fictício usado nos dados de demonstração. */
const NUMERO_DEMONSTRATIVO = '5521999999999';

/**
 * Mantém apenas os dígitos do número.
 * @param {string|null|undefined} numero
 * @returns {string}
 */
export function normalizeWhatsAppNumber(numero) {
  return String(numero ?? '').replace(/\D/g, '');
}

/**
 * Indica se o número é válido (10 a 15 dígitos, formato internacional).
 * @param {string|null|undefined} numero
 * @returns {boolean}
 */
export function isValidWhatsAppNumber(numero) {
  const digitos = normalizeWhatsAppNumber(numero);
  return digitos.length >= 10 && digitos.length <= 15;
}

/**
 * Indica se o número é o fictício do seed.
 * @param {string|null|undefined} numero
 * @returns {boolean}
 */
export function isDemoNumber(numero) {
  return normalizeWhatsAppNumber(numero) === NUMERO_DEMONSTRATIVO;
}

/**
 * Monta o link do WhatsApp, ou null quando não deve ser ativado.
 * @param {string|null|undefined} numero
 * @param {string} [mensagem]
 * @returns {string|null}
 */
export function buildWhatsAppUrl(numero, mensagem = '') {
  if (!isValidWhatsAppNumber(numero) || isDemoNumber(numero)) return null;
  const digitos = normalizeWhatsAppNumber(numero);
  const texto = mensagem ? `?text=${encodeURIComponent(mensagem)}` : '';
  return `https://wa.me/${digitos}${texto}`;
}

/**
 * Mensagem padrão para interesse em um serviço.
 * @param {string} nomeServico
 * @param {string} nomeBarbearia
 * @returns {string}
 */
export function buildServiceMessage(nomeServico, nomeBarbearia = 'Barbearia Vintage & Co.') {
  return `Olá! Tenho interesse no serviço "${nomeServico}" da ${nomeBarbearia}. Podemos combinar um horário?`;
}

/**
 * Mensagem genérica de contato.
 * @param {string} nomeBarbearia
 * @returns {string}
 */
export function buildGeneralMessage(nomeBarbearia = 'Barbearia Vintage & Co.') {
  return `Olá! Gostaria de agendar um atendimento na ${nomeBarbearia}.`;
}

/**
 * Gera o HTML do botão de WhatsApp.
 * Com número válido e real: link externo seguro (nova aba, rel="noopener noreferrer").
 * Com número ausente ou demonstrativo: elemento desabilitado e explicado.
 * @param {{numero?: string|null, mensagem?: string, rotulo?: string, classe?: string}} opcoes
 * @returns {object} HTML seguro.
 */
export function whatsappButton({
  numero,
  mensagem = '',
  rotulo = 'Falar pelo WhatsApp',
  classe = 'btn btn--primary',
}) {
  const url = buildWhatsAppUrl(numero, mensagem);
  if (url) {
    return html`<a class="${classe}" href="${url}" target="_blank" rel="noopener noreferrer">${rotulo}<span class="sr-only"> (abre em nova aba)</span></a>`;
  }
  return html`<span class="${classe} is-disabled" role="link" aria-disabled="true" title="WhatsApp indisponível: o número ainda é demonstrativo ou não foi configurado.">${rotulo}</span>`;
}