/**
 * Utilitários de tratamento de erros da API.
 * Cobre os status 0 (rede), 400, 401, 403, 404, 409, 429 e 500.
 */

/** Erro padronizado lançado pela camada de API. */
export class ApiError extends Error {
  /**
   * @param {number} status Código HTTP (0 = falha de rede/timeout).
   * @param {string} message Mensagem em português.
   * @param {any} [data] Corpo JSON da resposta, se houver.
   * @param {number|null} [retryAfter] Segundos para nova tentativa (429).
   */
  constructor(status, message, data = null, retryAfter = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
    this.retryAfter = retryAfter;
  }
}

/**
 * Extrai a primeira mensagem de texto de um valor retornado pela API.
 * @param {any} valor String, array ou objeto aninhado.
 * @returns {string}
 */
function primeiraMensagem(valor) {
  if (valor == null) return '';
  if (typeof valor === 'string') return valor;
  if (Array.isArray(valor)) return valor.map(primeiraMensagem).filter(Boolean).join(' ');
  if (typeof valor === 'object') {
    return Object.values(valor).map(primeiraMensagem).filter(Boolean).join(' ');
  }
  return String(valor);
}

/**
 * Separa erros por campo (400) do erro geral (detail / non_field_errors).
 * @param {any} data Corpo da resposta de erro.
 * @returns {{fields: Record<string,string>, general: string}}
 */
export function parseValidationErrors(data) {
  const fields = {};
  let general = '';
  if (!data || typeof data !== 'object') return { fields, general };

  for (const [chave, valor] of Object.entries(data)) {
    const mensagem = primeiraMensagem(valor);
    if (!mensagem) continue;
    if (chave === 'detail' || chave === 'non_field_errors') {
      general = general ? `${general} ${mensagem}` : mensagem;
    } else {
      fields[chave] = mensagem;
    }
  }
  return { fields, general };
}

/**
 * Converte qualquer erro em mensagem amigável em português.
 * @param {unknown} erro
 * @returns {string}
 */
export function getErrorMessage(erro) {
  if (!(erro instanceof ApiError)) {
    return 'Ocorreu um erro inesperado. Tente novamente.';
  }
  const { general, fields } = parseValidationErrors(erro.data);

  switch (erro.status) {
    case 0:
      return 'Não foi possível conectar ao servidor. Verifique sua conexão e se o backend está em execução.';
    case 400: {
      if (general) return general;
      const lista = Object.values(fields);
      return lista.length ? lista.join(' ') : 'Os dados enviados são inválidos. Revise o formulário.';
    }
    case 401:
    case 403:
      return general || 'Acesso negado. Entre novamente no painel administrativo.';
    case 404:
      return general || 'O registro solicitado não foi encontrado.';
    case 409:
      return general || 'Não foi possível concluir a ação por causa de um conflito com outros registros.';
    case 429:
      return erro.retryAfter
        ? `Muitas tentativas. Aguarde ${erro.retryAfter} segundos e tente novamente.`
        : 'Muitas tentativas em pouco tempo. Aguarde um momento e tente novamente.';
    default:
      if (erro.status >= 500) {
        return 'O servidor encontrou um problema. Tente novamente em instantes.';
      }
      return general || 'Não foi possível concluir a solicitação.';
  }
}