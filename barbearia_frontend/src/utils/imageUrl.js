/**
 * Resolução e validação segura de URLs de imagem e links externos.
 * Aceita URLs relativas (/media/...) e absolutas http/https.
 */

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');

/**
 * Verifica se uma URL usa apenas http ou https.
 * @param {string|null|undefined} url
 * @returns {boolean}
 */
export function isSafeHttpUrl(url) {
  if (!url || typeof url !== 'string') return false;
  try {
    const analisada = new URL(url, window.location.origin);
    return analisada.protocol === 'http:' || analisada.protocol === 'https:';
  } catch {
    return false;
  }
}

/**
 * Resolve o caminho de uma imagem retornado pela API.
 * @param {string|null|undefined} caminho Ex.: "/media/services/x.jpg" ou URL absoluta.
 * @returns {string|null} URL segura, ou null quando ausente/inválida.
 */
export function resolveImageUrl(caminho) {
  if (!caminho || typeof caminho !== 'string') return null;
  const valor = caminho.trim();
  if (!valor) return null;

  // Caminho relativo da API: usa a base configurada (ou a mesma origem, via proxy)
  if (valor.startsWith('/') && !valor.startsWith('//')) {
    const url = `${API_BASE}${valor}`;
    return isSafeHttpUrl(url) ? url : null;
  }
  return isSafeHttpUrl(valor) ? valor : null;
}

/**
 * Retorna a URL se for http/https; caso contrário, "#".
 * @param {string|null|undefined} url
 * @returns {string}
 */
export function safeLink(url) {
  return isSafeHttpUrl(url) ? url : '#';
}